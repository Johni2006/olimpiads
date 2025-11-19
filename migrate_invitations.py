"""
Скрипт для применения миграции системы приглашений
"""
import sqlite3
from pathlib import Path

def apply_migration():
    """Применить миграцию для системы приглашений"""
    db_path = Path(__file__).parent / "olympiad_questions.db"
    migration_path = Path(__file__).parent / "database" / "migration_invitations.sql"

    if not migration_path.exists():
        print(f"❌ Файл миграции не найден: {migration_path}")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        with open(migration_path, 'r', encoding='utf-8') as f:
            migration_sql = f.read()

        cursor.executescript(migration_sql)
        conn.commit()

        print("✅ Миграция системы приглашений успешно применена!")

        # Проверяем созданные таблицы
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name = 'quiz_invitations'
        """)
        if cursor.fetchone():
            print("✅ Таблица quiz_invitations создана")

        # Проверяем представление
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='view' AND name = 'invitation_details'
        """)
        if cursor.fetchone():
            print("✅ Представление invitation_details создано")

        # Проверяем новую колонку в quiz_attempts
        cursor.execute("PRAGMA table_info(quiz_attempts)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'invitation_id' in columns:
            print("✅ Колонка invitation_id добавлена в quiz_attempts")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ Ошибка при применении миграции: {e}")
        return False

if __name__ == "__main__":
    apply_migration()
