import json, socket, select, threading, time, hmac, hashlib, logging
from collections import defaultdict, deque

import wg_qrotator.exceptions as e
from wg_qrotator import constants

logger = logging.getLogger(__name__)


class SAE:
    def __init__(
        self, id: str, ip: str, port: int, sae_id: str, cert: str, key: str
    ) -> None:
        self.id = id
        self.ip = ip
        self.port = port
        self.sae_id = sae_id
        self.cert = cert
        self.key = key


class Communicator:
    def __init__(self, my_ip: str, my_port: int) -> None:
        self.my_ip = my_ip
        self.my_port = my_port
        self._msg_id = 0
        self._message_queues = defaultdict(
            lambda: deque(maxlen=constants.MAX_MESSAGE_QUEUE_SIZE)
        )
        self._ping_responses = {}
        self._running = threading.Event()
        self._id_lock = threading.Lock()
        self._ping_lock = threading.Lock()
        self._peer_cookies = {}
        self._peer_back_cookies = {}
        self._peer_hello_cookies = {}
        self._seen_nonces = defaultdict(lambda: deque(maxlen=10000))

    @staticmethod
    def is_acked(msg: dict, msg_id: int) -> bool:
        ack = msg.get("acked")
        if msg and ack and ack == msg_id:
            return True
        return False

    @staticmethod
    def is_abort(msg: dict) -> bool:
        msg_type = msg.get("msg_type")
        if not msg_type or msg_type == "Abort round":
            return True
        return False

    def _generate_nonce(
        self, peer_ip: str, msg_id: int, timestamp: float = None, source: str = None
    ) -> str:
        if peer_ip not in self._peer_cookies:
            raise ValueError("No shared key for peer")
        if timestamp is None:
            timestamp = time.time()

        key = self._peer_cookies[peer_ip]
        if source == "back": 
            key = self._peer_back_cookies[peer_ip]
        elif source == "hello":
            key = self._peer_hello_cookies[peer_ip]

        data = f"{msg_id}:{timestamp}".encode("utf-8")
        return hmac.new(key, data, hashlib.sha256).hexdigest(), timestamp

    def _verify_nonce(
        self, peer_ip: str, msg_id: int, timestamp: float, received_nonce: str, is_hello: bool = False
    ) -> bool:
        nonce_check = False
        if peer_ip not in self._peer_cookies:
            return False
        expected_nonce, _ = self._generate_nonce(peer_ip, msg_id, timestamp)
        if hmac.compare_digest(expected_nonce, received_nonce):
            nonce_check = True

        if not nonce_check and peer_ip in self._peer_back_cookies:
            expected_nonce_back, _ = self._generate_nonce(
                peer_ip, msg_id, timestamp, source="back"
            )
            if hmac.compare_digest(expected_nonce_back, received_nonce):
                nonce_check = True

        if not nonce_check and is_hello and peer_ip in self._peer_hello_cookies:
            expected_nonce_hello, _ = self._generate_nonce(
                peer_ip, msg_id, timestamp, source="hello"
            )
            if hmac.compare_digest(expected_nonce_hello, received_nonce):
                nonce_check = True

        if not nonce_check:
            return False

        if abs(time.time() - timestamp) > constants.NONCE_EXPIRY:
            return False

        if received_nonce in self._seen_nonces[peer_ip]:
            return False
        self._seen_nonces[peer_ip].append(received_nonce)
        return True

    def _receive_messages(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((self.my_ip, self.my_port))
            sock.listen(5)
            while self._running.is_set():
                # small timeout so we remain responsive to stop_listening()
                readable, _, _ = select.select([sock], [], [], 0.1)
                for readable_socket in readable:
                    client_socket, addr = readable_socket.accept()
                    with client_socket:
                        # Read the 4-byte message length first
                        header = client_socket.recv(4)
                        if not header:
                            continue

                        message_length = int.from_bytes(header, "big")

                        if (
                            message_length <= 0
                            or message_length > constants.MAX_MESSAGE_SIZE
                        ):
                            continue

                        # Read the full message based on length
                        data = b""
                        while len(data) < message_length:
                            packet = client_socket.recv(1024)
                            if not packet:
                                break
                            data += packet

                        if len(data) != message_length:
                            continue

                        # parse JSON once
                        try:
                            msg = json.loads(data.decode("utf-8"))
                        except Exception:
                            continue

                        self._process_incoming_message(msg, addr)

    def _process_incoming_message(self, msg: dict, addr) -> None:
        msg_type = msg.get("msg_type")
        peer_ip = addr[0]

        if peer_ip in self._peer_cookies:
            nonce = msg.get("nonce")
            timestamp = msg.get("timestamp")
            msg_id = msg.get("msg_id")
            if (
                not nonce
                or timestamp is None
                or not self._verify_nonce(
                    peer_ip, msg_id, timestamp, nonce, is_hello=msg_type == "Hello"
                )
            ):
                logger.info(f"Message from {addr} dropped due to invalid NONCE")
                return  # drop invalid or replayed message

        # Automatic ping reply: send pong back to sender's listening port.
        if msg_type == "Ping":
            # prefer src_port advertised by sender; fall back to TCP source port
            dst_port = msg.get("src_port", addr[1])
            try:
                pong = {"msg_type": "Pong", "msg_id": msg.get("msg_id")}
                # best-effort: use same raw sender->recipient socket path (separate connection)
                self._send_raw_message(pong, addr[0], dst_port)
            except Exception:
                # don't raise — keep this transparent
                pass
            return

        # If it's a Pong, signal the waiting event for that ping
        if msg_type == "Pong":
            with self._ping_lock:
                event = self._ping_responses.pop(msg.get("msg_id"), None)
            if event:
                event.set()
            return

        self._message_queues[addr[0]].append(json.dumps(msg))

    def _send_raw_message(self, message: dict, dst_ip: str, dst_port: int) -> None:
        if dst_ip in self._peer_cookies:
            if "msg_id" not in message:
                msg_id = self._get_next_msg_id()
                message["msg_id"] = msg_id
            else:
                msg_id = message["msg_id"]
            nonce, timestamp = self._generate_nonce(dst_ip, msg_id)
            message["nonce"] = nonce
            message["timestamp"] = timestamp
        else:
            raise e.No_cookie_set_for_peer_exception(f"No cookie for {dst_ip}")

        data = json.dumps(message).encode("utf-8")
        header = len(data).to_bytes(4, "big")
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1.0)
                sock.connect((dst_ip, dst_port))
                sock.sendall(header + data)
        except Exception:
            pass

    def _get_next_msg_id(self) -> int:
        with self._id_lock:
            self._msg_id += 1
            return self._msg_id

    def set_peer_cookie(self, peer_ip: str, cookie: bytes) -> None:
        self._peer_cookies[peer_ip] = cookie

    def set_peer_back_cookie(self, peer_ip: str, cookie: bytes) -> None:
        self._peer_back_cookies[peer_ip] = cookie

    def set_peer_hello_cookie(self, peer_ip: str, cookie: bytes) -> None:
        self._peer_hello_cookies[peer_ip] = cookie

    def get_peer_cookie(self, peer_ip: str) -> bytes:
        return self._peer_back_cookies.get(peer_ip)

    def wait_for_ack(
        self, period: float, max_tries: int, msg_id: int, other_sae_ip: str
    ) -> None:
        rcv_msg = self.wait_for_message(
            period, max_tries, other_sae_ip, message_types=["Ack"]
        )
        if not Communicator.is_acked(rcv_msg, msg_id):
            raise e.Connection_timeout(period*max_tries)

    def send_message(
        self,
        message: dict,
        dst_ip: str,
        dst_port: int,
        wait_for_ack: bool = False,
        timeout: int = 5,
    ) -> int:
        if dst_ip in self._peer_cookies:
            msg_id = self._get_next_msg_id()
            nonce, timestamp = self._generate_nonce(dst_ip, msg_id)
            message["msg_id"] = msg_id
            message["nonce"] = nonce
            message["timestamp"] = timestamp
        else:
            raise e.No_cookie_set_for_peer_exception(f"No cookie for {dst_ip}")

        message = json.dumps(message).encode("utf-8")

        # Add length prefix (4-byte big-endian)
        message_length = len(message)
        header = message_length.to_bytes(4, "big")  # 4-byte header

        start_time = time.time()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            while time.time() - start_time < timeout:
                try:
                    sock.connect((dst_ip, dst_port))
                    sock.sendall(header + message)  # Send header and message
                    if wait_for_ack:
                        self.wait_for_ack(0.0001, 100000, msg_id, dst_ip)
                    return msg_id
                except Exception:
                    time.sleep(0.5)  # Retry after delay
            raise e.Connection_timeout(timeout)

    def wait_for_message(
        self, period: float, max_tries: int, other_sae_ip: str, message_types: list = []
    ) -> dict:
        tries = 0
        while max_tries == -1 or tries < max_tries:
            time.sleep(period)
            tries += 1
            if self.has_messages_from(other_sae_ip):
                try:
                    msg = json.loads(self.get_message_from(other_sae_ip))
                except json.JSONDecodeError:
                    continue
                if msg.get("msg_type") not in message_types:
                    continue
                if Communicator.is_abort(msg):
                    e.Rotation_exception("Rotation round aborted")
                return msg
        raise e.Connection_timeout(period * max_tries)

    def start_listening(self) -> None:
        self._running.set()
        threading.Thread(target=self._receive_messages, daemon=True).start()

    def stop_listening(self) -> None:
        self._running.clear()

    def has_messages_from(self, ip) -> bool:
        return bool(self._message_queues[ip])

    def get_message_from(self, ip) -> str:
        return self._message_queues[ip].popleft() if self._message_queues[ip] else None

    def send_ping(self, dst_ip: str, dst_port: int, timeout: float = 2.0) -> bool:
        msg_id = self._get_next_msg_id()
        ping = {"msg_type": "Ping", "msg_id": msg_id, "src_port": self.my_port}

        event = threading.Event()
        with self._ping_lock:
            self._ping_responses[msg_id] = event

        # Fire-and-forget send; the reply will come back as a separate inbound connection
        self._send_raw_message(ping, dst_ip, dst_port)

        return event.wait(timeout)
