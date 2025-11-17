#!/bin/bash
# Скрипт синхронизации БД между корнем и api/

SOURCE_DB="olympiad_questions.db"
TARGET_DB="api/olympiad_questions.db"

# Проверить, какая БД новее
if [ ! -f "$SOURCE_DB" ]; then
    echo "❌ Источник $SOURCE_DB не найден"
    exit 1
fi

if [ ! -f "$TARGET_DB" ]; then
    echo "📋 Целевой файл не существует, копирую..."
    cp "$SOURCE_DB" "$TARGET_DB"
    echo "✅ БД скопирована в api/"
    exit 0
fi

# Сравнить время изменения
SOURCE_TIME=$(stat -f %m "$SOURCE_DB" 2>/dev/null || stat -c %Y "$SOURCE_DB")
TARGET_TIME=$(stat -f %m "$TARGET_DB" 2>/dev/null || stat -c %Y "$TARGET_DB")

if [ "$SOURCE_TIME" -gt "$TARGET_TIME" ]; then
    echo "📥 Корневая БД новее, синхронизирую api/..."
    cp "$SOURCE_DB" "$TARGET_DB"
    echo "✅ api/olympiad_questions.db обновлена"
elif [ "$TARGET_TIME" -gt "$SOURCE_TIME" ]; then
    echo "📤 БД в api/ новее, синхронизирую корень..."
    cp "$TARGET_DB" "$SOURCE_DB"
    echo "✅ olympiad_questions.db обновлена"
else
    echo "✓ БД синхронизированы (одинаковое время изменения)"
fi
