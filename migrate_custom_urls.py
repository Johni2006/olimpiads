"""
Миграция для добавления кастомных URL и контроля доступа к викторинам

Добавляет:
1. Поле custom_slug в таблицу quizzes для красивых URL
2. Таблицу quiz_access_control для белого списка email/доменов
"""

import sqlite3

DB_PATH = 'olympiad_questions.db'

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        print("🔄 Начинаем миграцию...")

        # 1. Добавляем поле custom_slug в таблицу quizzes
        print("📝 Добавляем поле custom_slug в таблицу quizzes...")
        try:
            cursor.execute("""
                ALTER TABLE quizzes
                ADD COLUMN custom_slug VARCHAR(100)
            """)
            print("✅ Поле custom_slug добавлено")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("⚠️  Поле custom_slug уже существует")
            else:
                raise

        # 2. Создаем уникальный индекс для custom_slug
        print("📝 Создаем уникальный индекс для custom_slug...")
        try:
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_quizzes_custom_slug
                ON quizzes(custom_slug) WHERE custom_slug IS NOT NULL
            """)
            print("✅ Уникальный индекс для custom_slug создан")
        except Exception as e:
            print(f"⚠️  Ошибка при создании индекса: {e}")

        # 3. Создаем таблицу для контроля доступа
        print("📝 Создаем таблицу quiz_access_control...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_access_control (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_id INTEGER NOT NULL,
                entry_type VARCHAR(20) NOT NULL,  -- 'email' или 'domain'
                entry_value VARCHAR(200) NOT NULL,  -- конкретный email или домен (@school.ru)
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(200),
                notes TEXT,
                FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE,
                UNIQUE(quiz_id, entry_type, entry_value)
            )
        """)
        print("✅ Таблица quiz_access_control создана")

        # 4. Создаем индексы для быстрого поиска
        print("📝 Создаем индексы для quiz_access_control...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_access_quiz
            ON quiz_access_control(quiz_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_access_type
            ON quiz_access_control(entry_type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_access_value
            ON quiz_access_control(entry_value)
        """)
        print("✅ Индексы созданы")

        # 5. Добавляем поле require_email_validation в quizzes
        print("📝 Добавляем поле require_email_validation в quizzes...")
        try:
            cursor.execute("""
                ALTER TABLE quizzes
                ADD COLUMN require_email_validation BOOLEAN DEFAULT 0
            """)
            print("✅ Поле require_email_validation добавлено")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("⚠️  Поле require_email_validation уже существует")
            else:
                raise

        conn.commit()
        print("✅ Миграция успешно завершена!")

    except Exception as e:
        conn.rollback()
        print(f"❌ Ошибка при миграции: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
