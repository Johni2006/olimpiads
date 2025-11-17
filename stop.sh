#!/bin/bash
# Скрипт для остановки системы олимпиадных вопросов

echo "🛑 Остановка системы..."
echo ""

cd "$(dirname "$0")"

# Останавливаем по сохраненным PID
if [ -f ".api.pid" ]; then
    API_PID=$(cat .api.pid)
    if ps -p $API_PID > /dev/null 2>&1; then
        echo "✓ Остановка API сервера (PID: $API_PID)..."
        kill $API_PID
    fi
    rm .api.pid
fi

if [ -f ".web.pid" ]; then
    WEB_PID=$(cat .web.pid)
    if ps -p $WEB_PID > /dev/null 2>&1; then
        echo "✓ Остановка веб-сервера (PID: $WEB_PID)..."
        kill $WEB_PID
    fi
    rm .web.pid
fi

# Дополнительно останавливаем по имени процесса
pkill -f "python.*api/app.py" 2>/dev/null || true
pkill -f "python.*http.server 8000" 2>/dev/null || true

echo ""
echo "✅ Система остановлена"
