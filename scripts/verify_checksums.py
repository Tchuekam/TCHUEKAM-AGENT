#!/usr/bin/env python3
"""
Supply-chain Verification Script for TCHUEKAM
Verifies the SHA-256 checksums of core Python files against checksums.json.
"""
import json
import hashlib
import sys
from pathlib import Path

def get_file_hash(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()

def main():
    base_dir = Path(__file__).resolve().parent.parent / "tchuekam-agent" / "app"
    checksum_file = base_dir / "checksums.json"
    
    if not checksum_file.exists():
        print("[-] checksums.json not found. To generate, run this script with --generate.")
        if len(sys.argv) > 1 and sys.argv[1] == "--generate":
            checksums = {}
            for py_file in base_dir.rglob("*.py"):
                rel_path = str(py_file.relative_to(base_dir)).replace("\\", "/")
                checksums[rel_path] = get_file_hash(py_file)
            with open(checksum_file, 'w') as f:
                json.dump(checksums, f, indent=4)
            print("[+] checksums.json generated successfully.")
            sys.exit(0)
        sys.exit(1)

    with open(checksum_file, 'r') as f:
        expected_checksums = json.load(f)

    mismatch = False
    for filename, expected_hash in expected_checksums.items():
        filepath = base_dir / filename
        if not filepath.exists():
            print(f"[!] Missing file: {filename}")
            mismatch = True
            continue
                
        actual_hash = get_file_hash(filepath)
        if actual_hash != expected_hash:
            print(f"[!] Checksum mismatch for {filename}: Expected {expected_hash}, got {actual_hash}")
            mismatch = True

    if mismatch:
        print("[-] Supply-chain verification FAILED! Exiting.")
        sys.exit(1)
    else:
        print("[+] Supply-chain verification PASSED. All core files are intact.")
        sys.exit(0)

if __name__ == "__main__":
    main()
