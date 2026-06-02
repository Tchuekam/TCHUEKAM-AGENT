import os
import logging
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = logging.getLogger("tchuekam.crypto")

class CryptoManager:
    """TCHUEKAM V1 Data-at-rest Encryption Protocol
    
    Ensures all sensitive state, logs, and model interactions 
    persisted to disk are encrypted via AES-256-GCM.
    """
    
    def __init__(self):
        # The key should be 32 bytes for AES-256
        # In production, this key must come from the Secret Manager vault
        key_hex = os.environ.get("TCHUEKAM_VAULT_AES_KEY")
        if not key_hex:
            logger.warning("[SECURE-VAULT] TCHUEKAM_VAULT_AES_KEY not set. Using ephemeral memory key for session.")
            self._key = AESGCM.generate_key(bit_length=256)
        else:
            self._key = bytes.fromhex(key_hex)
        self._aesgcm = AESGCM(self._key)

    def encrypt_data(self, plaintext: bytes) -> bytes:
        """Encrypt data using AES-256-GCM with a random nonce."""
        nonce = os.urandom(12)
        ciphertext = self._aesgcm.encrypt(nonce, plaintext, None)
        return nonce + ciphertext

    def decrypt_data(self, encrypted_data: bytes) -> bytes:
        """Decrypt AES-256-GCM encrypted data."""
        if len(encrypted_data) < 12:
            raise ValueError("Invalid ciphertext: too short")
        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]
        return self._aesgcm.decrypt(nonce, ciphertext, None)

_instance = None

def get_crypto_manager() -> CryptoManager:
    global _instance
    if _instance is None:
        _instance = CryptoManager()
    return _instance
