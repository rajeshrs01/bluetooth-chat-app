"""
encryption.py
End-to-end encryption for BlueChat messages using Fernet (AES-128-CBC + HMAC).

Key exchange flow:
  1. Both sides generate a keypair (RSA-2048).
  2. They swap public keys over the Bluetooth socket.
  3. One side generates a random Fernet session key,
     encrypts it with the remote public key, and sends it.
  4. All subsequent messages are encrypted with that session key.
"""

import os
import base64
from typing import Optional, Tuple

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives import serialization, hashes
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


class EncryptionManager:
    """Handles key generation, exchange, and symmetric encryption."""

    def __init__(self):
        self._fernet: Optional["Fernet"] = None
        self._private_key = None
        self._public_key = None
        self.enabled = False

    # ------------------------------------------------------------------ #
    #  Availability
    # ------------------------------------------------------------------ #

    @staticmethod
    def is_available() -> bool:
        return CRYPTO_AVAILABLE

    # ------------------------------------------------------------------ #
    #  Key generation
    # ------------------------------------------------------------------ #

    def generate_keypair(self):
        """Generate an RSA-2048 keypair."""
        if not CRYPTO_AVAILABLE:
            raise RuntimeError("cryptography package not installed.")
        self._private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        self._public_key = self._private_key.public_key()

    def get_public_key_bytes(self) -> bytes:
        """Serialize our public key to PEM bytes for sending over the wire."""
        return self._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

    # ------------------------------------------------------------------ #
    #  Session key (initiator side — sends encrypted session key)
    # ------------------------------------------------------------------ #

    def create_session_key(self, remote_public_key_pem: bytes) -> bytes:
        """
        Generate a Fernet session key, encrypt it with the remote's RSA
        public key, and return the encrypted blob to send.
        """
        session_key = Fernet.generate_key()
        self._fernet = Fernet(session_key)

        remote_pub = serialization.load_pem_public_key(remote_public_key_pem)
        encrypted_session_key = remote_pub.encrypt(
            session_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        self.enabled = True
        return encrypted_session_key

    # ------------------------------------------------------------------ #
    #  Session key (responder side — decrypts received session key)
    # ------------------------------------------------------------------ #

    def load_session_key(self, encrypted_session_key: bytes):
        """
        Decrypt the session key sent by the initiator using our private key.
        """
        session_key = self._private_key.decrypt(
            encrypted_session_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        self._fernet = Fernet(session_key)
        self.enabled = True

    # ------------------------------------------------------------------ #
    #  Encrypt / Decrypt
    # ------------------------------------------------------------------ #

    def encrypt(self, plaintext: str) -> bytes:
        """Encrypt a UTF-8 string. Returns raw encrypted bytes."""
        if not self.enabled or not self._fernet:
            return plaintext.encode("utf-8")
        return self._fernet.encrypt(plaintext.encode("utf-8"))

    def decrypt(self, ciphertext: bytes) -> str:
        """Decrypt bytes back to a UTF-8 string."""
        if not self.enabled or not self._fernet:
            return ciphertext.decode("utf-8", errors="replace")
        return self._fernet.decrypt(ciphertext).decode("utf-8")

    def encrypt_b64(self, plaintext: str) -> str:
        """Encrypt and return as base64 string (safe for text protocols)."""
        return base64.b64encode(self.encrypt(plaintext)).decode("ascii")

    def decrypt_b64(self, b64_ciphertext: str) -> str:
        """Decode base64 then decrypt."""
        return self.decrypt(base64.b64decode(b64_ciphertext))
