#!/bin/bash
# Скрипт резервного копирования базы данных

DB_FILE="olympiad_questions.db"
BACKUP_DIR="database/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/olympiad_questions_${TIMESTAMP}.db"

# Создать папку для бэкапов
mkdir -p "$BACKUP_DIR"

# Создать бэкап
echo "📦 Создание резервной копии БД..."
cp "$DB_FILE" "$BACKUP_FILE"

# Сжать старые бэкапы (старше 1 дня)
find "$BACKUP_DIR" -name "*.db" -mtime +1 -exec gzip {} \;

# Оставить только последние 30 бэкапов (несжатых)
ls -t "$BACKUP_DIR"/*.db 2>/dev/null | tail -n +31 | xargs -r rm

# Оставить только последние 100 сжатых бэкапов
ls -t "$BACKUP_DIR"/*.db.gz 2>/dev/null | tail -n +101 | xargs -r rm

echo "✅ Бэкап создан: $BACKUP_FILE"
echo "📊 Статистика бэкапов:"
echo "   Несжатых: $(ls -1 "$BACKUP_DIR"/*.db 2>/dev/null | wc -l)"
echo "   Сжатых: $(ls -1 "$BACKUP_DIR"/*.db.gz 2>/dev/null | wc -l)"
