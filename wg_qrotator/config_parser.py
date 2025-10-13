import yaml, ipaddress, os, subprocess
from schema import Schema, Optional

import wg_qrotator.exceptions as e
from wg_qrotator import constants

CONFIG_PATH = None


def is_ip(val: str) -> bool:
    """Check if IP address is valid.

    Args:
        val (str): arbitrary string.

    Returns:
        bool: True if val is a valid IP address, False if not.
    """
    try:
        ipaddress.ip_address(val)
        return True
    except ValueError:
        return False


def is_port(val: int) -> bool:
    """Check if port number is valid.

    Args:
        val (str): arbitrary integer.

    Returns:
        bool: True if val is a valid port number, False if not.
    """
    return 0 < val < 65536


def file_exists(path: str) -> bool:
    """Check if path exists in the filesystem.

    Args:
        val (str): arbitrary string.

    Returns:
        bool: True if val is a valid path, False if not.
    """
    path_ = path
    if not os.path.isabs(path):
        path_ = os.path.join(os.path.dirname(os.path.abspath(CONFIG_PATH)), path)

    return os.path.isfile(path_)


def is_mode(val: str) -> bool:
    """Check if it is valid mode.

    Args:
        val (str): arbitrary string.

    Returns:
        bool: True if val is a valid mode, False if not.
    """
    return val in ("client", "server")


def kem_is_supported(kem: str) -> bool:
    """Check if KEM is supported.

    Args:
        val (str): arbitrary string.

    Returns:
        bool: True if val is a valid and supported KEM identifier, False if not.
    """
    return kem in constants.SUPPORTED_KEMS


def kms_interface_is_supported(interface: int) -> bool:
    """Check if KMS interface standard is supported.

    Args:
        val (int): arbitrary integer.

    Returns:
        bool: True if val is a valid and supported KMS interface identifier, False if not.
    """
    return interface in constants.SUPPORTED_KMS_INTERFACES


def is_valid_wg_interface(interface_name: str) -> bool:
    """Check WireGuard network interface exists.

    Args:
        interface_name (str): network interface name

    Returns:
        bool: True if the interface is a valid WireGuard network interface, False if not.
    """
    result = subprocess.check_output(["wg", "show", "interfaces"], text=True)
    interfaces = result.strip().split()
    return interface_name in interfaces


schema = Schema(
    {
        Optional("debug"): bool,
        "interface": is_valid_wg_interface,
        "kms": {
            "uri": str,
            "certificate": file_exists,
            "root_certificate": file_exists,
            "secret_key": file_exists,
            "sae": str,
            "interface": kms_interface_is_supported,
        },
        "ip": is_ip,
        "port": is_port,
        "peers": [
            {
                str: {
                    "ip": is_ip,
                    "port": is_port,
                    "sae": str,
                    "mode": is_mode,
                    Optional("extra_handshakes"): [
                        {
                            kem_is_supported: {
                                "secret_key": file_exists,
                                "public_key": file_exists,
                            }
                        }
                    ],
                }
            }
        ],
    }
)


def validate_config(config: dict) -> bool:
    """Validate configuration file data.

    Args:
        config (dict): configuration data.

    Raises:
        e.Config_exception: when a an error is found in the configuration data.

    Returns:
        bool: validation results.
    """
    try:
        return schema.validate(config)
    except Exception as err:
        raise e.Config_exception(f"Invalid configuration: {err}")


def read_config(config_filename: str) -> dict:
    """Read, parse, and validate configuration file.

    Args:
        config_filename (str): Path of the configuration file.

    Raises:
        e.Config_exception: When file does not exist or cannot be read.
        e.Config_exception: When configuration data is not valid.

    Returns:
        dict: configuration data
    """
    global CONFIG_PATH
    CONFIG_PATH = config_filename
    try:
        with open(config_filename, "r") as file:
            config: dict = yaml.safe_load(file)
    except:
        raise e.Config_exception(f"Cannot parse {config_filename}")

    if not config or not validate_config(config):
        raise e.Config_exception(f"Invalid configuration in {config_filename}")

    return config
