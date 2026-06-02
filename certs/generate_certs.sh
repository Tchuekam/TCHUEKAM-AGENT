#!/bin/bash
# TCHUEKAM Code Assistant in Google One AI Pro
# Protocol: Transport Security (TLS 1.3)
# Action: Generate self-signed certificates for local development and validation.

set -e

CERT_DIR="$(dirname "$0")"
mkdir -p "$CERT_DIR"

echo "[TCHUEKAM] Generating TLS 1.3 compliant local certificates..."

openssl req -x509 -nodes -days 365 -newkey rsa:4096 \
    -keyout "$CERT_DIR/tchuekam-key.pem" \
    -out "$CERT_DIR/tchuekam-cert.pem" \
    -subj "/C=US/ST=State/L=City/O=Tchuekam/OU=Security/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

chmod 600 "$CERT_DIR/tchuekam-key.pem"
chmod 644 "$CERT_DIR/tchuekam-cert.pem"

echo "[TCHUEKAM] Certificates generated successfully."
echo "Cert: $CERT_DIR/tchuekam-cert.pem"
echo "Key: $CERT_DIR/tchuekam-key.pem"
