#!/bin/bash

# Test bot endpoints with curl
# This validates the bot is listening and responding to health checks

set -e

BOT_TOKEN="123456:ABCDEF"
OWNER_ID="1"
STORAGE_CHANNEL_ID="1"
MAIN_CHANNEL_ID="1"
DATABASE_URL="sqlite+aiosqlite:///tmp/bot_test.db"
WEBHOOK_URL="http://localhost:8080"
PORT="8080"

export BOT_TOKEN OWNER_ID STORAGE_CHANNEL_ID MAIN_CHANNEL_ID DATABASE_URL WEBHOOK_URL PORT

echo "=== Starting Bot in WEBHOOK Mode ==="
cd /workspaces/medlocum_content_bot

# Start bot in background
python -m bot.main > /tmp/bot.log 2>&1 &
BOT_PID=$!
echo "Bot PID: $BOT_PID"

# Wait for startup
sleep 4

echo ""
echo "=== Testing Health Endpoint ==="
curl -s -w "\nHTTP Status: %{http_code}\n" http://localhost:${PORT}/health

echo ""
echo "=== Testing Webhook Path Exists ==="
curl -s -w "\nHTTP Status: %{http_code}\n" \
  -X POST \
  -H "X-Telegram-Bot-Api-Secret-Token: invalid" \
  "http://localhost:${PORT}/webhook/${BOT_TOKEN}" \
  -d '{}' 2>&1 | head -20

echo ""
echo "=== Testing Invalid Secret Token ==="
curl -s -w "\nHTTP Status: %{http_code}\n" \
  -X POST \
  -H "X-Telegram-Bot-Api-Secret-Token: wrong-token" \
  "http://localhost:${PORT}/webhook/${BOT_TOKEN}" \
  -d '{}' 2>&1 | head -20

echo ""
echo "=== Bot Logs ==="
tail -30 /tmp/bot.log

echo ""
echo "=== Cleanup ==="
kill $BOT_PID 2>/dev/null || true
sleep 1
echo "Test complete"
