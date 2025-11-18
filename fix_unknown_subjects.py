#!/usr/bin/env python3
"""
Скрипт для обновления subject у PDF файлов где subject='unknown'
Извлекает предмет из имени файла
"""

import sqlite3
import re
from pathlib import Path

# Маппинг префиксов имен файлов на предметы
SUBJECT_MAPPING = {
    'biology': 'Биология',
    'bio': 'Биология',
    'chem': 'Химия',
    'chemistry': 'Химия',
    'math': 'Математика',
    'phys': 'Физика',
    'physics': 'Физика',
    'philos': 'Философия',
    'philosophy': 'Философия',
    'history': 'История',
    'hist': 'История',
    'relig': 'Религиоведение',
    'religion': 'Религиоведение',
    'polit': 'Политология',
    'journal': 'Журналистика',
    'pravo': 'Право',
    'law': 'Право',
    'obshestvo': 'Обществознание',
    'social': 'Обществознание',
    'soci': 'Обществознание',
    'econ': 'Экономика',
    'econom': 'Экономика',
    'ecology': 'Экология',
    'ecol': 'Экология',
    'foreign': 'Иностранный язык',
    'english': 'Иностранный язык',
    'german': 'Иностранный язык',
    'french': 'Иностранный язык',
    'geography': 'География',
    'geogr': 'География',
    'geo_': 'География',
    'geology': 'Геология',
    'geol': 'Геология',
    'inform': 'Информатика',
    'comp': 'Информатика',
    'liter': 'Литература',
    'lit_': 'Литература',
    'rus': 'Русский язык',
    'russian': 'Русский язык',
    'astro': 'Астрономия',
    'psycho': 'Психология',
    'педагог': 'Педагогика',
    'pedagog': 'Педагогика',
    'mechanics': 'Механика',
    'mechan': 'Механика',
    'lang_': 'Иностранный язык',
}

def extract_subject_from_filename(filename: str) -> str:
    """Извлечь предмет из имени файла"""
    filename_lower = filename.lower()

    # Проверяем каждый префикс
    for prefix, subject in SUBJECT_MAPPING.items():
        if filename_lower.startswith(prefix):
            return subject

    return None

def main():
    db_path = Path(__file__).parent / 'api' / 'olympiad_questions.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Получаем все PDF с subject='unknown'
    cursor.execute("""
        SELECT id, file_path, display_name
        FROM pdf_files
        WHERE subject = 'unknown' OR subject IS NULL
    """)

    unknown_pdfs = cursor.fetchall()
    print(f"Найдено {len(unknown_pdfs)} PDF файлов с неизвестным предметом")

    updated = 0
    not_found = 0

    for pdf_id, file_path, display_name in unknown_pdfs:
        # Пробуем извлечь предмет из display_name
        subject = extract_subject_from_filename(display_name)

        if subject:
            print(f"  {display_name} → {subject}")
            cursor.execute("""
                UPDATE pdf_files
                SET subject = ?
                WHERE id = ?
            """, (subject, pdf_id))
            updated += 1
        else:
            if not_found < 10:  # Показываем первые 10
                print(f"  ⚠ Не удалось определить предмет: {display_name}")
            not_found += 1

    conn.commit()
    print(f"\n✅ Обновлено: {updated}")
    print(f"❌ Не определено: {not_found}")

    # Показываем статистику по предметам
    cursor.execute("""
        SELECT subject, COUNT(*) as cnt
        FROM pdf_files
        WHERE subject IS NOT NULL
        GROUP BY subject
        ORDER BY cnt DESC
    """)

    print("\nСтатистика по предметам:")
    for subject, cnt in cursor.fetchall():
        print(f"  {subject}: {cnt}")

    conn.close()

if __name__ == '__main__':
    main()
