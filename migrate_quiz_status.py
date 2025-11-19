#!/usr/bin/env python3
"""
Миграция: добавление поля status в таблицу quizzes
"""
import sqlite3
import os

# Путь к БД
DB_PATH = os.path.join(os.path.dirname(__file__), 'olympiad_questions.db')

def migrate():
    """Добавить поле status в таблицу quizzes"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Проверяем, существует ли уже поле status
        cursor.execute("PRAGMA table_info(quizzes)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'status' not in columns:
            print("Добавляем поле 'status' в таблицу quizzes...")
            cursor.execute("""
                ALTER TABLE quizzes ADD COLUMN status VARCHAR(20) DEFAULT 'draft'
            """)

            # Устанавливаем статус 'draft' для всех существующих викторин
            cursor.execute("""
                UPDATE quizzes SET status = 'draft' WHERE status IS NULL
            """)

            conn.commit()
            print("✅ Поле 'status' успешно добавлено!")
        else:
            print("ℹ️  Поле 'status' уже существует")

    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
