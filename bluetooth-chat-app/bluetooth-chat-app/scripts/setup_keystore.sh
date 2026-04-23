#!/bin/bash
# setup_keystore.sh
# Run this ONCE on your local machine to create your signing keystore.
# Then upload the output values to GitHub Secrets.

set -e

KEY_ALIAS="bluechat"
KEYSTORE_FILE="bluechat.keystore"
VALIDITY_DAYS=10000

echo "=== BlueChat APK Signing Keystore Setup ==="
echo ""
echo "You will be prompted for:"
echo "  - Keystore password (remember this!)"
echo "  - Your name, org, city, country"
echo ""

keytool -genkey -v \
  -keystore "$KEYSTORE_FILE" \
  -alias "$KEY_ALIAS" \
  -keyalg RSA \
  -keysize 2048 \
  -validity "$VALIDITY_DAYS"

echo ""
echo "=== Keystore created: $KEYSTORE_FILE ==="
echo ""
echo "Now add these to GitHub → Settings → Secrets → Actions:"
echo ""
echo "1. KEYSTORE_BASE64"
echo "   Value:"
base64 -w 0 "$KEYSTORE_FILE"
echo ""
echo ""
echo "2. KEYSTORE_PASSWORD  →  the password you just entered"
echo "3. KEY_ALIAS          →  bluechat"
echo "4. KEY_PASSWORD       →  same as keystore password (or separate if you set one)"
echo ""
echo "KEEP bluechat.keystore safe — losing it means you can't update the app!"
