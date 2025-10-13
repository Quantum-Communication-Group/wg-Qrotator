import base64
import sys
from wolfcrypt.ciphers import MlKemPrivate

from wg_qrotator import handshake


def gen_priv_key(kem: str):
    """Generate private key encoded as base64 for the provided KEM and output it to stdout.

    Args:
        kem (str): KEM identifier.
    """
    kem_type = handshake.get_alg(kem)

    kem_priv = MlKemPrivate.make_key(kem_type)
    b64priv_key = base64.b64encode(kem_priv.encode_priv_key())

    print(b64priv_key.decode())


def gen_pub_key(kem: str):
    """Generate public key encoded as base64 from private key retrieved from stdin for the
    provided KEM and output it to stdout.

    Args:
        kem (str): KEM identifier.
    """
    kem_type = handshake.get_alg(kem)
    kem_priv = MlKemPrivate(kem_type)

    b64_priv_key = sys.stdin.read()

    priv_bytes = base64.b64decode(b64_priv_key)
    kem_priv.decode_key(priv_bytes)

    pub_key = kem_priv.encode_pub_key()
    b64pub_key = base64.b64encode(pub_key)

    print(b64pub_key.decode())
