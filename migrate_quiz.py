#!/usr/bin/env python3
"""
Миграция базы данных для добавления функционала викторин
"""
import sqlite3
from pathlib import Path

def migrate_database(db_path: str):
    """Применить миграцию для викторин"""
    print(f"🔄 Применение миграции к базе данных: {db_path}")

    # Читаем SQL миграцию
    migration_path = Path(__file__).parent / "database" / "quiz_schema.sql"

    if not migration_path.exists():
        print(f"❌ Файл миграции не найден: {migration_path}")
        return False

    with open(migration_path, 'r', encoding='utf-8') as f:
        migration_sql = f.read()

    # Применяем миграцию
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Разбиваем на отдельные команды
        # SQLite не поддерживает IF NOT EXISTS для ALTER TABLE, поэтому обрабатываем ошибки
        statements = migration_sql.split(';')

        for statement in statements:
            statement = statement.strip()
            if not statement:
                continue

            try:
                cursor.execute(statement)
                conn.commit()
            except sqlite3.OperationalError as e:
                error_msg = str(e).lower()
                # Игнорируем ошибки о том, что колонка уже существует
                if 'duplicate column' in error_msg or 'already exists' in error_msg:
                    print(f"  ⚠️  {statement[:50]}... (уже существует)")
                    continue
                else:
                    print(f"  ❌ Ошибка: {e}")
                    print(f"     SQL: {statement[:100]}...")
                    raise

        print("✅ Миграция успешно применена")

        # Проверяем созданные таблицы
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name LIKE '%quiz%'
            ORDER BY name
        """)

        tables = [row[0] for row in cursor.fetchall()]
        print(f"\n📊 Таблицы викторин в базе данных:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  - {table}: {count} записей")

        return True

    except Exception as e:
        print(f"❌ Ошибка при применении миграции: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    # Применяем миграцию к основной базе
    db_paths = [
        "olympiad_questions.db",
        "api/olympiad_questions.db"
    ]

    for db_path in db_paths:
        if Path(db_path).exists():
            print(f"\n{'='*60}")
            migrate_database(db_path)
        else:
            print(f"⚠️  База данных не найдена: {db_path}")

    print("\n✅ Миграция завершена для всех баз данных")
