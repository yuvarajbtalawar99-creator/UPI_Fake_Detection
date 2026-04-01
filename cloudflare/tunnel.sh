#!/bin/bash

# ==============================================================================
# KAVACH – Cloudflare Tunnel Setup Helper
# This script guides you through exposing your local FastAPI backend to the internet.
# ==============================================================================

echo "------------------------------------------------------------"
echo "  KAVACH Cloudflare Tunnel Setup helper"
echo "------------------------------------------------------------"

# 1. Install cloudflared (Manual step depending on OS)
# Download: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/install-and-setup/installation/

# 2. Login to Cloudflare
# cloudflared tunnel login

# 3. Create a tunnel
# cloudflared tunnel create kavach-backend

# 4. Create a configuration file (config.yml) or use the dashboard.
# Recommended: Use the Cloudflare Zero Trust dashboard for easier management.

# 5. Route traffic (example)
# cloudflared tunnel route dns kavach-backend api.yourdomain.com

# 6. Run the tunnel (assuming local port 8000)
# cloudflared tunnel run --url http://localhost:8000 kavach-backend

echo "Setup Steps:"
echo "1. Run: cloudflared tunnel login"
echo "2. Run: cloudflared tunnel create kavach-backend"
echo "3. Run: cloudflared tunnel route dns kavach-backend api.yourdomain.com"
echo "4. Run: cloudflared tunnel run --url http://localhost:8000 kavach-backend"
echo "------------------------------------------------------------"
echo "Once the tunnel is running, update your frontend/js/config.js to use:"
echo "API_BASE_URL: 'https://api.yourdomain.com'"
echo "------------------------------------------------------------"
