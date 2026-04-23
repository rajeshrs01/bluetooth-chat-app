"""
test_encryption.py
Unit tests for EncryptionManager.
"""

import pytest

try:
    from src.core.encryption import EncryptionManager
    CRYPTO_AVAILABLE = EncryptionManager.is_available()
except ImportError:
    CRYPTO_AVAILABLE = False


@pytest.mark.skipif(not CRYPTO_AVAILABLE, reason="cryptography not installed")
class TestEncryptionManager:

    def test_encrypt_decrypt_roundtrip(self):
        """Alice encrypts, Bob decrypts — same session key path."""
        alice = EncryptionManager()
        bob = EncryptionManager()

        alice.generate_keypair()
        bob.generate_keypair()

        # Bob sends his public key to Alice; Alice creates session key
        encrypted_session_key = alice.create_session_key(bob.get_public_key_bytes())

        # Alice sends encrypted session key to Bob; Bob loads it
        bob.load_session_key(encrypted_session_key)

        message = "Hello, Bob! 🔒"
        ciphertext = alice.encrypt_b64(message)
        decrypted = bob.decrypt_b64(ciphertext)

        assert decrypted == message

    def test_encrypt_returns_different_bytes(self):
        """Same plaintext should yield different ciphertexts (Fernet uses random IV)."""
        mgr = EncryptionManager()
        mgr.generate_keypair()
        # Self-session for isolation test
        from cryptography.fernet import Fernet
        key = Fernet.generate_key()
        from cryptography.fernet import Fernet as F
        mgr._fernet = F(key)
        mgr.enabled = True

        c1 = mgr.encrypt_b64("test")
        c2 = mgr.encrypt_b64("test")
        assert c1 != c2  # different IVs

    def test_disabled_passthrough(self):
        """When encryption is disabled, encrypt/decrypt are pass-through."""
        mgr = EncryptionManager()
        mgr.enabled = False
        result = mgr.encrypt("hello")
        assert result == b"hello"
        assert mgr.decrypt(b"hello") == "hello"
