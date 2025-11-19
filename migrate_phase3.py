"""
Скрипт для применения миграции Фазы 3
"""
import sqlite3
from pathlib import Path

def apply_migration():
    """Применить миграцию для Фазы 3"""
    db_path = Path(__file__).parent / "olympiad_questions.db"
    migration_path = Path(__file__).parent / "database" / "migration_phase3.sql"

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

        print("✅ Миграция Фазы 3 успешно применена!")

        # Проверяем созданные таблицы
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name IN ('teacher_notes', 'attempt_tags')
        """)
        tables = cursor.fetchall()
        print(f"✅ Созданные таблицы: {[t[0] for t in tables]}")

        # Проверяем представления
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='view' AND name IN ('student_stats', 'attempt_details')
        """)
        views = cursor.fetchall()
        print(f"✅ Созданные представления: {[v[0] for v in views]}")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ Ошибка при применении миграции: {e}")
        return False

if __name__ == "__main__":
    apply_migration()
