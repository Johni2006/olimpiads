#!/usr/bin/env python3
"""
Миграция: расширение функциональности управления PDF файлами и вопросами
Добавляет новые поля для:
- Типа файла (олимпиада/викторина)
- Сложности файла
- SHA256 хеша для дедупликации
- Информации о скачивании
- Статуса проверки вопросов
- Цифровой шкалы сложности вопросов
"""
import sqlite3
import hashlib
import os
from pathlib import Path

DB_PATH = "olympiad_questions.db"
PARSER_VERSION = "1.0.0"

def calculate_file_hash(file_path):
    """Вычисление SHA256 хеша файла"""
    if not os.path.exists(file_path):
        return None

    try:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        print(f"   ⚠️  Ошибка при вычислении hash для {file_path}: {e}")
        return None

def calculate_verification_status(conn, file_path):
    """Автоматический расчет статуса проверки на основе вопросов"""
    cursor = conn.cursor()

    # Общее количество вопросов
    cursor.execute("""
        SELECT COUNT(*) FROM questions WHERE source_pdf = ?
    """, (file_path,))
    total = cursor.fetchone()[0]

    if total == 0:
        return 'not_verified'

    # Количество проверенных вопросов
    cursor.execute("""
        SELECT COUNT(*) FROM questions
        WHERE source_pdf = ? AND verified = 1
    """, (file_path,))
    verified = cursor.fetchone()[0]

    if verified == total:
        return 'verified'
    elif verified > 0:
        return 'partially_verified'
    else:
        return 'not_verified'

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("🔧 МИГРАЦИЯ: Расширение функциональности PDF файлов")
    print("=" * 60)

    # ========================================================================
    # 1. ДОБАВЛЕНИЕ НОВЫХ КОЛОНОК В pdf_files
    # ========================================================================

    print("\n📦 Добавление новых колонок в таблицу pdf_files...")

    # Проверка существующих колонок
    cursor.execute("PRAGMA table_info(pdf_files)")
    existing_columns = {row[1] for row in cursor.fetchall()}

    new_columns = {
        'file_type': "ALTER TABLE pdf_files ADD COLUMN file_type VARCHAR DEFAULT 'olympiad'",
        'difficulty': "ALTER TABLE pdf_files ADD COLUMN difficulty INTEGER DEFAULT NULL",
        'file_hash': "ALTER TABLE pdf_files ADD COLUMN file_hash VARCHAR(64) DEFAULT NULL",
        'download_source': "ALTER TABLE pdf_files ADD COLUMN download_source VARCHAR DEFAULT NULL",
        'archive_source': "ALTER TABLE pdf_files ADD COLUMN archive_source VARCHAR DEFAULT NULL",
        'is_from_archive': "ALTER TABLE pdf_files ADD COLUMN is_from_archive BOOLEAN DEFAULT 0",
        'verification_status': "ALTER TABLE pdf_files ADD COLUMN verification_status VARCHAR DEFAULT 'not_verified'",
        'manual_verification_override': "ALTER TABLE pdf_files ADD COLUMN manual_verification_override BOOLEAN DEFAULT 0",
        'last_parsed_at': "ALTER TABLE pdf_files ADD COLUMN last_parsed_at TIMESTAMP DEFAULT NULL",
        'parser_version': "ALTER TABLE pdf_files ADD COLUMN parser_version VARCHAR DEFAULT NULL"
    }

    added_count = 0
    for col_name, sql in new_columns.items():
        if col_name not in existing_columns:
            cursor.execute(sql)
            print(f"   ✅ Добавлена колонка: {col_name}")
            added_count += 1
        else:
            print(f"   ⏭️  Колонка уже существует: {col_name}")

    print(f"\n   Добавлено новых колонок: {added_count}")

    # ========================================================================
    # 2. ДОБАВЛЕНИЕ НОВЫХ КОЛОНОК В questions
    # ========================================================================

    print("\n📦 Добавление новых колонок в таблицу questions...")

    cursor.execute("PRAGMA table_info(questions)")
    existing_columns = {row[1] for row in cursor.fetchall()}

    if 'numeric_difficulty' not in existing_columns:
        cursor.execute("ALTER TABLE questions ADD COLUMN numeric_difficulty INTEGER DEFAULT NULL")
        print("   ✅ Добавлена колонка: numeric_difficulty")
    else:
        print("   ⏭️  Колонка уже существует: numeric_difficulty")

    conn.commit()

    # ========================================================================
    # 3. СОЗДАНИЕ ИНДЕКСОВ
    # ========================================================================

    print("\n📑 Создание индексов для производительности...")

    indexes = [
        ("idx_pdf_files_hash", "CREATE INDEX IF NOT EXISTS idx_pdf_files_hash ON pdf_files(file_hash)"),
        ("idx_pdf_files_file_type", "CREATE INDEX IF NOT EXISTS idx_pdf_files_file_type ON pdf_files(file_type)"),
        ("idx_pdf_files_difficulty", "CREATE INDEX IF NOT EXISTS idx_pdf_files_difficulty ON pdf_files(difficulty)"),
        ("idx_pdf_files_verification", "CREATE INDEX IF NOT EXISTS idx_pdf_files_verification ON pdf_files(verification_status)"),
        ("idx_questions_source_verified", "CREATE INDEX IF NOT EXISTS idx_questions_source_verified ON questions(source_pdf, verified)"),
        ("idx_questions_numeric_difficulty", "CREATE INDEX IF NOT EXISTS idx_questions_numeric_difficulty ON questions(numeric_difficulty)")
    ]

    for idx_name, idx_sql in indexes:
        cursor.execute(idx_sql)
        print(f"   ✅ Создан индекс: {idx_name}")

    conn.commit()

    # ========================================================================
    # 4. СОЗДАНИЕ ТРИГГЕРА ДЛЯ АВТООБНОВЛЕНИЯ verification_status
    # ========================================================================

    print("\n⚡ Создание триггера автообновления verification_status...")

    # Удалить старый триггер если существует
    cursor.execute("DROP TRIGGER IF EXISTS update_pdf_verification_status")

    # Создать триггер
    cursor.execute("""
        CREATE TRIGGER update_pdf_verification_status
        AFTER UPDATE OF verified ON questions
        FOR EACH ROW
        WHEN (SELECT manual_verification_override FROM pdf_files WHERE file_path = NEW.source_pdf) = 0
        BEGIN
            UPDATE pdf_files
            SET verification_status = (
                CASE
                    WHEN (SELECT COUNT(*) FROM questions WHERE source_pdf = NEW.source_pdf AND verified = 1) =
                         (SELECT COUNT(*) FROM questions WHERE source_pdf = NEW.source_pdf)
                    THEN 'verified'
                    WHEN (SELECT COUNT(*) FROM questions WHERE source_pdf = NEW.source_pdf AND verified = 1) > 0
                    THEN 'partially_verified'
                    ELSE 'not_verified'
                END
            )
            WHERE file_path = NEW.source_pdf;
        END
    """)

    print("   ✅ Триггер создан: update_pdf_verification_status")

    conn.commit()

    # ========================================================================
    # 5. ВЫЧИСЛЕНИЕ SHA256 ДЛЯ СУЩЕСТВУЮЩИХ ФАЙЛОВ
    # ========================================================================

    print("\n🔐 Вычисление SHA256 хешей для существующих файлов...")

    cursor.execute("SELECT id, file_path, file_hash FROM pdf_files")
    all_pdfs = cursor.fetchall()

    processed = 0
    skipped = 0
    errors = 0

    for pdf_id, file_path, existing_hash in all_pdfs:
        if existing_hash:
            skipped += 1
            continue

        file_hash = calculate_file_hash(file_path)

        if file_hash:
            cursor.execute("""
                UPDATE pdf_files
                SET file_hash = ?
                WHERE id = ?
            """, (file_hash, pdf_id))
            processed += 1

            if processed % 50 == 0:
                print(f"   Обработано: {processed} файлов...")
                conn.commit()
        else:
            errors += 1

    conn.commit()

    print(f"   ✅ Обработано: {processed}")
    print(f"   ⏭️  Пропущено (уже есть hash): {skipped}")
    print(f"   ⚠️  Ошибок: {errors}")

    # ========================================================================
    # 6. АВТОМАТИЧЕСКИЙ РАСЧЕТ verification_status
    # ========================================================================

    print("\n✔️  Расчет статуса проверки для всех файлов...")

    cursor.execute("SELECT id, file_path, verification_status FROM pdf_files")
    all_pdfs = cursor.fetchall()

    status_counts = {'verified': 0, 'partially_verified': 0, 'not_verified': 0}

    for pdf_id, file_path, current_status in all_pdfs:
        new_status = calculate_verification_status(conn, file_path)

        cursor.execute("""
            UPDATE pdf_files
            SET verification_status = ?
            WHERE id = ?
        """, (new_status, pdf_id))

        status_counts[new_status] += 1

    conn.commit()

    print(f"   ✅ Проверено файлов: {status_counts['verified']}")
    print(f"   ⚠️  Частично проверено: {status_counts['partially_verified']}")
    print(f"   ❌ Не проверено: {status_counts['not_verified']}")

    # ========================================================================
    # 7. СТАТИСТИКА
    # ========================================================================

    print("\n📊 ИТОГОВАЯ СТАТИСТИКА")
    print("=" * 60)

    # Общее количество PDF
    cursor.execute("SELECT COUNT(*) FROM pdf_files")
    total_pdfs = cursor.fetchone()[0]
    print(f"Всего PDF файлов: {total_pdfs}")

    # С хешами
    cursor.execute("SELECT COUNT(*) FROM pdf_files WHERE file_hash IS NOT NULL")
    with_hash = cursor.fetchone()[0]
    print(f"С SHA256 хешем: {with_hash}")

    # Общее количество вопросов
    cursor.execute("SELECT COUNT(*) FROM questions")
    total_questions = cursor.fetchone()[0]
    print(f"Всего вопросов: {total_questions}")

    # Проверенные вопросы
    cursor.execute("SELECT COUNT(*) FROM questions WHERE verified = 1")
    verified_questions = cursor.fetchone()[0]
    print(f"Проверенных вопросов: {verified_questions}")

    # Дубликаты по hash
    cursor.execute("""
        SELECT file_hash, COUNT(*) as cnt
        FROM pdf_files
        WHERE file_hash IS NOT NULL
        GROUP BY file_hash
        HAVING cnt > 1
    """)
    duplicates = cursor.fetchall()

    if duplicates:
        print(f"\n⚠️  ВНИМАНИЕ: Обнаружено {len(duplicates)} дубликатов по hash:")
        for hash_val, count in duplicates:
            print(f"   Hash {hash_val[:16]}... встречается {count} раз(а)")
    else:
        print("\n✅ Дубликаты не обнаружены")

    print("\n✅ МИГРАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
    print("=" * 60)

    conn.close()

if __name__ == "__main__":
    migrate()
