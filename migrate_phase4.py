"""
Скрипт для применения миграции Фазы 4
"""
import sqlite3
from pathlib import Path

def apply_migration():
    """Применить миграцию для Фазы 4"""
    db_path = Path(__file__).parent / "olympiad_questions.db"
    migration_path = Path(__file__).parent / "database" / "migration_phase4.sql"

    if not migration_path.exists():
        print(f"❌ Файл миграции не найден: {migration_path}")
        return False

    try:
        # Подключаемся к БД
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Читаем миграцию
        with open(migration_path, 'r', encoding='utf-8') as f:
            migration_sql = f.read()

        # Применяем миграцию
        cursor.executescript(migration_sql)
        conn.commit()

        print("✅ Миграция Фазы 4 успешно применена!")

        # Проверяем добавленные колонки
        cursor.execute("PRAGMA table_info(quizzes)")
        quiz_columns = [col[1] for col in cursor.fetchall()]
        ai_quiz_cols = [c for c in quiz_columns if 'ai_' in c]
        print(f"✅ Колонки AI в таблице quizzes: {ai_quiz_cols}")

        cursor.execute("PRAGMA table_info(quiz_answers)")
        answer_columns = [col[1] for col in cursor.fetchall()]
        ai_answer_cols = [c for c in answer_columns if 'ai_' in c]
        print(f"✅ Колонки AI в таблице quiz_answers: {ai_answer_cols}")

        cursor.execute("PRAGMA table_info(quiz_attempts)")
        attempt_columns = [col[1] for col in cursor.fetchall()]
        ai_attempt_cols = [c for c in attempt_columns if 'ai_' in c]
        print(f"✅ Колонки AI в таблице quiz_attempts: {ai_attempt_cols}")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ Ошибка при применении миграции: {e}")
        return False

if __name__ == "__main__":
    apply_migration()
