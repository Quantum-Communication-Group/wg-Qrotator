import argparse
import subprocess
import sys
import os
import signal
import time
import getpass
import psutil

from wg_qrotator import constants, key_gen, storage, config_parser


def up(config_file_or_interface_name: str) -> int:
    """`up` command handler.

    Args:
        config_file_or_interface_name (str): config file path or interface name.

    Returns:
        int: return code (0 indicates success)
    """
    state = storage.Wg_qrotator_state.load()

    if (
        config_file_or_interface_name in state.interfaces.keys()
        and state.interfaces[config_file_or_interface_name].status
        != storage.InterfaceStatus.DOWN
    ):
        print(f"Interface is not down. Stop it first", file=sys.stderr)
        return 1
    else:
        if config_file_or_interface_name in state.interfaces:
            config_file = state.interfaces.get(
                config_file_or_interface_name).config_file
        else:
            config_file = config_file_or_interface_name
        if (
            config_parser.read_config(config_file)
        ):
            import keyring
            from keyrings.alt.file import EncryptedKeyring

            kr = EncryptedKeyring()
            if not kr._check_file():
                keyring.set_keyring(kr)
                keyring.set_password(f"wg_qrotator", "wg", f"{time.time()}")
            env = os.environ.copy()
            env["KEYRING_PASSWORD"] = getpass.getpass(
                "Enter keyring password to unlock it: "
            )
            try:
                subprocess.Popen(
                    [
                        sys.executable,
                        os.path.join(os.path.dirname(__file__), "qrotator.py"),
                        config_file_or_interface_name,
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    env=env,
                )
            except Exception as e:
                print(f"Failed to start rotator: {e}", file=sys.stderr)
                return 1

            return 0


def down(interface_name: str) -> int:
    """`down` command handler.

    Args:
        interface (str): interface name.

    Returns:
        int: return code (0 indicates success)
    """
    state = storage.Wg_qrotator_state.load()
    if interface_name in state.interfaces and state.interfaces[interface_name].status in [
        storage.InterfaceStatus.UP,
        storage.InterfaceStatus.HOLDING,
    ]:
        print(f"Stopping rotator for interface {interface_name}")
        try:
            os.kill(state.interfaces.get(interface_name).pid, signal.SIGTERM)
            while psutil.pid_exists(state.interfaces.get(interface_name).pid):
                time.sleep(1)
        except ProcessLookupError:
            state.update_interface_status(
                interface_name, storage.InterfaceStatus.DOWN)
        return 0
    if interface_name in state.interfaces and state.interfaces[interface_name].status == storage.InterfaceStatus.DOWN:
        print(f"{interface_name} is already down!")
        return 0
    else:
        print(f"Invalid interface {interface_name}", file=sys.stderr)
        return 1


def rm(interface_name: str, force: bool = False):
    """`rm` command handler.

    Args:
        interface (str): interface name.

    Returns:
        int: return code (0 indicates success)
    """
    state = storage.Wg_qrotator_state.load()
    if interface_name in state.interfaces:
        if state.interfaces.get(interface_name).status in [
            storage.InterfaceStatus.DOWN,
            storage.InterfaceStatus.ERROR,
        ]:
            print(f"Removing interface {interface_name}")
            try:
                config = config_parser.read_config(
                    state.interfaces.get(interface_name).config_file)
                for peer in config["peers"]:
                    peer_ip = list(peer.values())[0]["ip"]
                    clear_cookie(interface_name, peer_ip)
            except:
                if not force:
                    print(f"Configuration file of the tunnel is not valid. Use the same command with the '-f' flag to force its removal.", file=sys.stderr)
                    return 1
                else:
                    print(f"Rotator removed but cookies were not cleared. Use the 'clearcookie' command to do so.")
            state.remove_interface(interface_name)
            return 0
        else:
            print(f"Cannot remove active rotator. Stop it first.", file=sys.stderr)
    else:
        print(f"Invalid interface {interface_name}", file=sys.stderr)

    return 1


def ls() -> int:
    """`ls` command handler.

    Returns:
        int: return code (0 indicates success)
    """
    state = storage.Wg_qrotator_state.load()
    state.formatted_print()
    return 0


def gen_priv_key(kem: str) -> int:
    """`genprivkey` command handler.

    Args:
        kem (str): KEM identifier

    Returns:
        int: return code
    """
    key_gen.gen_priv_key(kem)
    return 0


def gen_pub_key(kem: str) -> int:
    """`genpubkey` command handler.

    Args:
        kem (str): KEM identifier

    Returns:
        int: return code
    """
    key_gen.gen_pub_key(kem)
    return 0


def clear_cookie(interface_name: str, peer_ip: str) -> int:
    """`clearcookie` command handler.

    Returns:
        int: return code (0 indicates success)
    """
    import keyring
    import tempfile
    from keyrings.alt.file import EncryptedKeyring
    from filelock import FileLock

    LOCK_PATH = os.environ.get("WG_QROTATOR_KEYRING_LOCK") or os.path.join(
        tempfile.gettempdir(), "wg_qrotator_keyring.lock"
    )
    lock = FileLock(LOCK_PATH)

    keyring.set_keyring(EncryptedKeyring())
    try:
        with lock:
            keyring.delete_password(
                f"wg_qrotator", f"{interface_name}_{peer_ip}")
    except:
        print("Error while deleting cookie", file=sys.stderr)
        return 1
    return 0


HANDLER = {
    "up": up,
    "down": down,
    "rm": rm,
    "ls": ls,
    "genprivkey": gen_priv_key,
    "genpubkey": gen_pub_key,
    "clearcookie": clear_cookie,
}


def main() -> int:
    """CLI entrypoint.

    Returns:
        int: return code
    """
    parser = argparse.ArgumentParser(
        prog="wg-qrotator",
        description=f"Wg-Qrotator (v{constants.VERSION}) - The quantum-enabled hybrid key rotator for WireGuard tunnels.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # up command
    parser_up = subparsers.add_parser("up", help="start a rotator")
    parser_up.add_argument(
        "config_file_or_interface_name", help="path to the rotator's config file or, if rotator already exists, interface name"
    )

    # down command
    parser_down = subparsers.add_parser("down", help="stop a rotator")
    parser_down.add_argument("interface_name", help="interface name")

    # rm command
    parser_rm = subparsers.add_parser("rm", help="remove a rotator")
    parser_rm.add_argument("interface_name", help="interface name")
    parser_rm.add_argument(
        "-f", "--force",
        action="store_true",
        help="force removal (no confirmation)"
    )

    # genprivkey command
    parser_genprivkey = subparsers.add_parser(
        "genprivkey", help="generate private key")
    parser_genprivkey.add_argument(
        "kem",
        help=f"Key Encapsulation Mechanism identifier. Options: {constants.SUPPORTED_KEMS}",
    )

    # gen_pub_key command
    parser_genpubkey = subparsers.add_parser(
        "genpubkey", help="generate public key from private key"
    )
    parser_genpubkey.add_argument(
        "kem",
        help=f"Key Encapsulation Mechanism identifier. Options: {constants.SUPPORTED_KEMS}",
    )

    # clear_cookie
    parser_clear_cookie = subparsers.add_parser(
        "clearcookie", help="clear peer's cookie"
    )
    parser_clear_cookie.add_argument("interface_name", help="interface name")
    parser_clear_cookie.add_argument(
        "peer_ip", help="peer IP address"
    )

    # ls
    subparsers.add_parser("ls", help="list rotators")

    args = parser.parse_args()

    # Dispatch to handler
    kwargs = vars(args).copy()
    command = kwargs.pop("command")
    return_code = HANDLER[command](**kwargs)

    return return_code
