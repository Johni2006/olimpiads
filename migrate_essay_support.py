#!/usr/bin/env python3
"""
Миграция: добавление поддержки типа вопроса "эссе"
Добавляет поле для рекомендаций по оцениванию эссе
"""
import sqlite3

DB_PATH = "olympiad_questions.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("🔧 МИГРАЦИЯ: Добавление поддержки типа вопроса 'эссе'")
    print("=" * 60)

    # Проверка существующих колонок
    cursor.execute("PRAGMA table_info(questions)")
    existing_columns = {row[1] for row in cursor.fetchall()}

    if 'essay_guidelines' not in existing_columns:
        print("\n📦 Добавление поля essay_guidelines в таблицу questions...")
        cursor.execute("""
            ALTER TABLE questions
            ADD COLUMN essay_guidelines TEXT DEFAULT NULL
        """)
        print("   ✅ Поле добавлено: essay_guidelines")
    else:
        print("   ⏭️  Поле уже существует: essay_guidelines")

    conn.commit()

    # Статистика по типам вопросов
    print("\n📊 СТАТИСТИКА ПО ТИПАМ ВОПРОСОВ:")
    cursor.execute("""
        SELECT type, COUNT(*) as count
        FROM questions
        GROUP BY type
        ORDER BY count DESC
    """)

    for qtype, count in cursor.fetchall():
        print(f"   {qtype:20s}: {count:6d} вопросов")

    # Проверка изображений в вариантах
    print("\n🖼️  СТАТИСТИКА ИЗОБРАЖЕНИЙ:")
    cursor.execute("""
        SELECT COUNT(*) FROM images WHERE question_id IS NOT NULL AND option_id IS NULL
    """)
    question_images = cursor.fetchone()[0]
    print(f"   Изображений в вопросах: {question_images}")

    cursor.execute("""
        SELECT COUNT(*) FROM images WHERE option_id IS NOT NULL
    """)
    option_images = cursor.fetchone()[0]
    print(f"   Изображений в вариантах: {option_images}")

    print("\n✅ МИГРАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
    print("=" * 60)
    print("\nТеперь поддерживается:")
    print("  - Тип вопроса 'essay' для эссе")
    print("  - Поле essay_guidelines для рекомендаций по оцениванию")
    print("  - Изображения в вариантах ответов (уже работает)")

    conn.close()

if __name__ == "__main__":
    migrate()
