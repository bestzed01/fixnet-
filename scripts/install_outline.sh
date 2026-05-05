#!/bin/bash
# Run on Ubuntu VPS as root: sudo bash scripts/install_outline.sh
# Takes ~3 minutes. At the end it prints your OUTLINE_API_URL.
set -e
bash -c "$(wget -qO- https://raw.githubusercontent.com/Jigsaw-Code/outline-server/master/src/server_manager/install_scripts/install_server.sh)"
echo ""
echo "Copy the apiUrl above → paste as OUTLINE_API_URL in your .env"
