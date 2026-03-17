#!/bin/bash
# Deploy WebSocket service to Fly.io

echo "🚀 Deploying WebSocket service to Fly.io..."

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
    echo "❌ flyctl is not installed. Please install it first:"
    echo "   https://fly.io/docs/hands-on/install-flyctl/"
    exit 1
fi

# Check if logged in
if ! flyctl auth whoami &> /dev/null; then
    echo "❌ Not logged in to Fly.io. Please run: flyctl auth login"
    exit 1
fi

# Create app if it doesn't exist
if ! flyctl apps list | grep -q "chatapp-websockets"; then
    echo "📱 Creating Fly.io app..."
    flyctl apps create chatapp-websockets
fi

# Deploy
echo "🔧 Deploying WebSocket service..."
flyctl deploy --dockerfile Dockerfile.websocket

# Check status
echo "📊 Checking deployment status..."
flyctl status

echo "✅ WebSocket service deployed!"
echo "🔗 WebSocket URL: wss://chatapp-websockets.fly.dev"
echo ""
echo "Next steps:"
echo "1. Set WEBSOCKET_SERVICE_URL=wss://chatapp-websockets.fly.dev in Render"
echo "2. Test at: https://chatapp-1-kctm.onrender.com/websocket-debug/"