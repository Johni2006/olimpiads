#!/usr/bin/env python3
"""
Миграция: обновление представления quiz_stats для поддержки поля status
"""
import sqlite3
import os

# Путь к БД
DB_PATH = os.path.join(os.path.dirname(__file__), 'olympiad_questions.db')

def migrate():
    """Обновить представление quiz_stats"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        print("Пересоздаем представление quiz_stats...")

        # Удаляем старое представление
        cursor.execute("DROP VIEW IF EXISTS quiz_stats")

        # Создаем новое представление с полем status
        cursor.execute("""
            CREATE VIEW quiz_stats AS
            SELECT
                q.id,
                q.title,
                q.unique_code,
                q.created_at,
                q.is_active,
                q.status,
                q.description,
                q.created_by,
                COUNT(DISTINCT qa.id) as total_attempts,
                COUNT(DISTINCT CASE WHEN qa.completed_at IS NOT NULL THEN qa.id END) as completed_attempts,
                AVG(CASE WHEN qa.completed_at IS NOT NULL THEN qa.score END) as avg_score,
                COUNT(DISTINCT CASE WHEN qa.is_passed = 1 THEN qa.id END) as passed_count,
                (SELECT COUNT(*) FROM quiz_questions WHERE quiz_id = q.id) as question_count
            FROM quizzes q
            LEFT JOIN quiz_attempts qa ON q.id = qa.quiz_id
            GROUP BY q.id
        """)

        conn.commit()
        print("✅ Представление quiz_stats успешно обновлено!")

    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
