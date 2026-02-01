#!/bin/bash
# Start PAEA: docker services + ngrok + auto-set Telegram webhook

set -e

# Load .env
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "🚀 Starting Docker services..."
docker compose -f ~/PAEA/docker-compose.yml up -d 

echo "⏳ Waiting for app to be ready..."
until curl -s http://localhost:8000/health > /dev/null 2>&1; do
    sleep 1
done
echo "✅ App is healthy"

# Kill existing ngrok if running
pkill -f "ngrok http" 2>/dev/null || true
sleep 1

echo "🌐 Starting ngrok..."
ngrok http 8000 --log=stdout > /dev/null &
sleep 3

# Get ngrok public URL
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
tunnels = json.load(sys.stdin)['tunnels']
for t in tunnels:
    if t['proto'] == 'https':
        print(t['public_url'])
        break
" 2>/dev/null)

if [ -z "$NGROK_URL" ]; then
    echo "❌ Failed to get ngrok URL"
    exit 1
fi

echo "🔗 Ngrok URL: $NGROK_URL"

# Set Telegram webhook
echo "📡 Setting Telegram webhook..."
RESULT=$(curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
    -H "Content-Type: application/json" \
    -d "{\"url\": \"${NGROK_URL}/webhook/telegram\", \"secret_token\": \"${TELEGRAM_WEBHOOK_SECRET}\"}")

echo "$RESULT" | python3 -c "
import sys, json
r = json.load(sys.stdin)
if r.get('ok'):
    print('✅ Webhook set successfully')
else:
    print(f'❌ Webhook failed: {r}')
"

echo ""
echo "🎉 PAEA is running!"
echo "   App:     http://localhost:8000"
echo "   Ngrok:   $NGROK_URL"
echo "   Logs:    make logs-app"
echo "   Stop:    make down && pkill ngrok"
