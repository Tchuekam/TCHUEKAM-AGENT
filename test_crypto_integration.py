import sys
from pathlib import Path
import json

app_dir = Path(r"d:\TCHUEKAMV1\tchuekam-agent\app")
sys.path.insert(0, str(app_dir))

# pyrefly: ignore [missing-import]
from tchuekam_state import SessionDB
# pyrefly: ignore [missing-import]
from crypto_manager import get_crypto_manager

def test_encryption():
    # 1. Test Crypto Manager
    cm = get_crypto_manager()
    plaintext = b"Hello, Sovereign AI!"
    ciphertext = cm.encrypt_data(plaintext)
    decrypted = cm.decrypt_data(ciphertext)
    assert plaintext == decrypted, "CryptoManager failed basic encryption/decryption"
    print("[+] CryptoManager: Encryption/Decryption works.")

    # 2. Test SessionDB _encode_content and _decode_content
    # Test dictionary
    msg_dict = {"role": "user", "content": "Test message"}
    encoded = SessionDB._encode_content(msg_dict)
    assert isinstance(encoded, bytes), "_encode_content did not return bytes"
    decoded = SessionDB._decode_content(encoded)
    assert decoded == msg_dict, f"Dict decode failed: {decoded}"
    print("[+] SessionDB: Dictionary encryption/decryption works.")

    # Test plain string
    msg_str = "Just a string message"
    encoded_str = SessionDB._encode_content(msg_str)
    assert isinstance(encoded_str, bytes), "_encode_content did not return bytes for string"
    decoded_str = SessionDB._decode_content(encoded_str)
    assert decoded_str == msg_str, f"String decode failed: {decoded_str}"
    print("[+] SessionDB: String encryption/decryption works.")

    # 3. Test Logging Formatter
    # pyrefly: ignore [missing-import]
    from tchuekam_logging import setup_logging
    import logging
    import tempfile
    
    with tempfile.TemporaryDirectory() as td:
        setup_logging(tchuekam_home=Path(td), force=True)
        root = logging.getLogger()
        formatter = root.handlers[0].formatter
        
        # Mock a log record
        record = logging.LogRecord("test_logger", logging.INFO, "test.py", 42, "This is a test log message", (), None)
        record.session_tag = "[session-123]"
        
        formatted_json = formatter.format(record)
        
        parsed = json.loads(formatted_json)
        assert "signature" in parsed, "Signature missing from log JSON"
        assert parsed["signature"] != "UNSIGNED", "Log signature failed to generate"
        assert "This is a test log message" in parsed["message"], "Message missing or incorrect"
        print("[+] SecureJSONFormatter: Successfully generated signed JSON log.")
        print("    Log output preview:", formatted_json)

if __name__ == "__main__":
    test_encryption()
