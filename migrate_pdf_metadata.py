#!/usr/bin/env python3
"""
Миграция: создание таблицы метаданных PDF файлов
"""
import sqlite3
from pathlib import Path

DB_PATH = "olympiad_questions.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("📦 Создание таблицы pdf_files...")

    # Создать таблицу
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pdf_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL UNIQUE,
            display_name TEXT NOT NULL,
            university TEXT,
            olympiad TEXT,
            year TEXT,
            subject TEXT,
            is_manual BOOLEAN DEFAULT 0,
            question_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Создать индексы
    print("📑 Создание индексов...")
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_pdf_files_university ON pdf_files(university)",
        "CREATE INDEX IF NOT EXISTS idx_pdf_files_olympiad ON pdf_files(olympiad)",
        "CREATE INDEX IF NOT EXISTS idx_pdf_files_year ON pdf_files(year)",
        "CREATE INDEX IF NOT EXISTS idx_pdf_files_subject ON pdf_files(subject)",
        "CREATE INDEX IF NOT EXISTS idx_pdf_files_path ON pdf_files(file_path)",
    ]

    for index_sql in indexes:
        cursor.execute(index_sql)

    # Создать триггер
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_pdf_files_timestamp
        AFTER UPDATE ON pdf_files
        BEGIN
            UPDATE pdf_files SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END
    """)

    print("📥 Импорт существующих PDF из questions...")

    # Получить все уникальные PDF файлы из вопросов
    cursor.execute("""
        SELECT source_pdf, COUNT(*) as question_count
        FROM questions
        WHERE source_pdf IS NOT NULL
        GROUP BY source_pdf
    """)

    pdf_files = cursor.fetchall()
    print(f"   Найдено {len(pdf_files)} уникальных PDF файлов")

    # Вставить PDF файлы
    for file_path, question_count in pdf_files:
        # Извлечь имя файла из пути
        display_name = Path(file_path).name

        cursor.execute("""
            INSERT OR IGNORE INTO pdf_files (file_path, display_name, question_count)
            VALUES (?, ?, ?)
        """, (file_path, display_name, question_count))

    print("🏷️  Обновление метаданных из тегов...")

    # Обновить метаданные из тегов
    cursor.execute("""
        SELECT pdf.id, pdf.file_path
        FROM pdf_files pdf
    """)

    all_pdfs = cursor.fetchall()

    for pdf_id, file_path in all_pdfs:
        # Получить теги первого вопроса из этого PDF
        cursor.execute("""
            SELECT t.category, t.value
            FROM questions q
            JOIN tags t ON q.id = t.question_id
            WHERE q.source_pdf = ?
            LIMIT 100
        """, (file_path,))

        tags = cursor.fetchall()

        # Собрать метаданные
        metadata = {}
        for category, value in tags:
            if category in ['university', 'subject', 'year'] and category not in metadata:
                metadata[category] = value

        # Обновить PDF если есть метаданные
        if metadata:
            update_parts = []
            values = []

            if 'university' in metadata:
                update_parts.append("university = ?")
                values.append(metadata['university'])

            if 'subject' in metadata:
                update_parts.append("subject = ?")
                values.append(metadata['subject'])

            if 'year' in metadata:
                update_parts.append("year = ?")
                values.append(metadata['year'])

            if update_parts:
                values.append(pdf_id)
                cursor.execute(f"""
                    UPDATE pdf_files
                    SET {', '.join(update_parts)}
                    WHERE id = ?
                """, values)

    conn.commit()

    # Статистика
    cursor.execute("SELECT COUNT(*) FROM pdf_files")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pdf_files WHERE university IS NOT NULL OR subject IS NOT NULL")
    with_metadata = cursor.fetchone()[0]

    print(f"\n✅ Миграция завершена!")
    print(f"   Всего PDF: {total}")
    print(f"   С метаданными: {with_metadata}")

    conn.close()

if __name__ == "__main__":
    migrate()
