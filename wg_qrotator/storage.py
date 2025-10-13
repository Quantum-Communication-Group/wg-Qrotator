from dataclasses import dataclass
from typing import Dict
from enum import Enum
from datetime import datetime
import json
import os
from filelock import FileLock
import tempfile


class InterfaceStatus(Enum):
    UP = "up"
    DOWN = "down"
    HOLDING = "holding"
    ERROR = "error"


@dataclass
class WireGuardInterface:
    status: InterfaceStatus
    last_key_rotation: datetime
    pid: int
    config_file: str


class Wg_qrotator_state:
    TMP_DIR = os.path.join(tempfile.gettempdir(), "wg_qrotator")
    os.makedirs(TMP_DIR, exist_ok=True)
    STATE_FILE = os.path.join(TMP_DIR, "wg_qrotator_state.json")
    LOCK_FILE = STATE_FILE + ".lock"

    def __init__(self, interfaces: Dict[str, WireGuardInterface]):
        self.interfaces = interfaces

    @classmethod
    def load(cls) -> "Wg_qrotator_state":
        with FileLock(cls.LOCK_FILE):
            if not os.path.exists(cls.STATE_FILE):
                with open(cls.STATE_FILE, "w") as f:
                    f.write("{}")
                return cls({})
            with open(cls.STATE_FILE, "r") as f:
                raw = json.loads(f.read())

        interfaces = {
            name: WireGuardInterface(
                status=InterfaceStatus(data["status"]),
                last_key_rotation=datetime.fromisoformat(
                    data["last_key_rotation"])
                if data["last_key_rotation"]
                else None,
                pid=data["pid"],
                config_file=data["config_file"]
            )
            for name, data in raw.items()
        }
        return cls(interfaces)

    def _update_from_file(self):
        """Reload in-memory state from file. Caller must hold the lock."""
        if not os.path.exists(self.STATE_FILE):
            self.interfaces = {}
            return
        with open(self.STATE_FILE, "r") as f:
            raw = json.loads(f.read())

        self.interfaces = {
            name: WireGuardInterface(
                status=InterfaceStatus(data["status"]),
                last_key_rotation=datetime.fromisoformat(
                    data["last_key_rotation"])
                if data["last_key_rotation"]
                else None,
                pid=data["pid"],
                config_file=data["config_file"]
            )
            for name, data in raw.items()
        }

    def _to_json(self) -> str:
        return json.dumps(
            {
                name: {
                    "status": iface.status.value,
                    "last_key_rotation": iface.last_key_rotation.isoformat()
                    if iface.last_key_rotation
                    else None,
                    "pid": iface.pid,
                    "config_file": iface.config_file
                }
                for name, iface in self.interfaces.items()
            },
            indent=2,
        )

    def _write_file(self):
        with open(self.STATE_FILE, "w") as f:
            f.write(self._to_json())

    def update(self):
        with FileLock(self.LOCK_FILE):
            self._update_from_file()

    def update_rotation_timestamp(self, interface_name: str):
        with FileLock(self.LOCK_FILE):
            self._update_from_file()
            if interface_name in self.interfaces:
                self.interfaces[interface_name].last_key_rotation = datetime.now()
            self._write_file()

    def add_interface(self, interface_name: str, interface_info: WireGuardInterface):
        with FileLock(self.LOCK_FILE):
            self._update_from_file()
            self.interfaces[interface_name] = interface_info
            self._write_file()

    def remove_interface(self, interface_name: str):
        with FileLock(self.LOCK_FILE):
            self._update_from_file()
            self.interfaces.pop(interface_name, None)
            self._write_file()

    def update_interface_status(self, interface_name: str, status: InterfaceStatus):
        with FileLock(self.LOCK_FILE):
            self._update_from_file()
            if interface_name in self.interfaces:
                self.interfaces[interface_name].status = status
            self._write_file()

    def formatted_print(self):
        self._update_from_file()
        if not self.interfaces:
            print("No rotators found")
            return

        name_width = max(len(name) for name in self.interfaces.keys())
        status_width = max(len(iface.status.value) for iface in self.interfaces.values())
        last_key_rotation_width = max(
            len(iface.last_key_rotation.isoformat() if iface.last_key_rotation else "never")
            for iface in self.interfaces.values()
        )

        header = f"{'Interface':<{name_width}}  {'Status':<{status_width}}  {'Last Key Rotation':<{last_key_rotation_width}}"
        print(header)
        print("-" * len(header))

        for name, iface in self.interfaces.items():
            print(
                f"{name:<{max(name_width, 9)}}  "
                f"{iface.status.value:<{max(status_width, 6)}}  "
                f"{iface.last_key_rotation.isoformat() if iface.last_key_rotation else 'never'}"
            )

