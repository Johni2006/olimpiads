#!/bin/bash
# Скрипт для запуска системы олимпиадных вопросов

echo "🎓 Запуск системы олимпиадных вопросов"
echo "======================================"
echo ""

# Переходим в директорию проекта
cd "$(dirname "$0")"

# Активируем виртуальное окружение
if [ ! -d "venv" ]; then
    echo "❌ Виртуальное окружение не найдено!"
    echo "   Создайте его командой: python3 -m venv venv"
    exit 1
fi

echo "✓ Активация виртуального окружения..."
source venv/bin/activate

# Проверяем наличие БД
if [ ! -f "olympiad_questions.db" ]; then
    echo "⚠️  База данных не найдена, создаю новую..."
    python -c "from database.db_manager import DatabaseManager; DatabaseManager('olympiad_questions.db')"
fi

# Синхронизируем БД
if [ -f "olympiad_questions.db" ]; then
    echo "✓ Синхронизация базы данных..."
    cp olympiad_questions.db api/olympiad_questions.db
fi

# Останавливаем старые процессы API (если есть)
echo "✓ Проверка запущенных процессов..."
pkill -f "python.*api/app.py" 2>/dev/null || true

# Запускаем API сервер
echo "✓ Запуск API сервера на http://localhost:5001..."
cd api
nohup python app.py > api.log 2>&1 &
API_PID=$!
cd ..

# Ждем запуска API
sleep 2

# Проверяем, что API запустился
if curl -s http://localhost:5001/api/health > /dev/null 2>&1; then
    echo "✅ API сервер запущен (PID: $API_PID)"
else
    echo "⚠️  API сервер не отвечает, проверьте логи в api/api.log"
fi

# Запускаем веб-сервер для фронтенда
echo "✓ Запуск веб-сервера на http://localhost:8000..."
cd web
python -m http.server 8000 > ../web.log 2>&1 &
WEB_PID=$!
cd ..

sleep 1

echo ""
echo "======================================"
echo "✅ Система запущена!"
echo "======================================"
echo ""
echo "📍 Доступные адреса:"
echo "   • Веб-интерфейс:  http://localhost:8000"
echo "   • API:            http://localhost:5001"
echo ""
echo "📝 Процессы:"
echo "   • API сервер PID: $API_PID"
echo "   • Веб сервер PID: $WEB_PID"
echo ""
echo "🛑 Для остановки используйте: ./stop.sh"
echo "   или вручную: kill $API_PID $WEB_PID"
echo ""

# Сохраняем PID для скрипта остановки
echo "$API_PID" > .api.pid
echo "$WEB_PID" > .web.pid

# Открываем браузер (опционально)
if command -v open &> /dev/null; then
    echo "🌐 Открываем браузер..."
    sleep 1
    open http://localhost:8000
fi

echo "📖 Для просмотра логов:"
echo "   • API:  tail -f api/api.log"
echo "   • Web:  tail -f web.log"
echo ""
