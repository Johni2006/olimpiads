"""
Скрипт для поиска и удаления вопросов без вариантов ответа

Удаляет:
1. Вопросы типа 'choice' или 'multiple_choice' без вариантов ответа в таблице options
2. Вопросы типа 'matching' без пар в таблице matching_pairs
"""

import sqlite3
import argparse
from pathlib import Path


def find_invalid_questions(db_path: str = "olympiad_questions.db"):
    """Найти вопросы без вариантов ответа"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("🔍 Поиск вопросов без вариантов ответа...\n")

    # 1. Вопросы choice/multiple_choice без options
    cursor.execute("""
        SELECT q.id, q.text, q.type, q.source_pdf
        FROM questions q
        WHERE q.type IN ('choice', 'multiple_choice')
        AND NOT EXISTS (
            SELECT 1 FROM options o WHERE o.question_id = q.id
        )
        ORDER BY q.id
    """)

    choice_questions = cursor.fetchall()

    # 2. Вопросы matching без matching_pairs
    cursor.execute("""
        SELECT q.id, q.text, q.type, q.source_pdf
        FROM questions q
        WHERE q.type = 'matching'
        AND NOT EXISTS (
            SELECT 1 FROM matching_pairs mp WHERE mp.question_id = q.id
        )
        ORDER BY q.id
    """)

    matching_questions = cursor.fetchall()

    conn.close()

    return choice_questions, matching_questions


def display_invalid_questions(choice_questions, matching_questions):
    """Показать найденные невалидные вопросы"""
    total = len(choice_questions) + len(matching_questions)

    if total == 0:
        print("✅ Невалидных вопросов не найдено!")
        return False

    print(f"⚠️  Найдено {total} невалидных вопросов:\n")

    if choice_questions:
        print(f"📝 Вопросы choice/multiple_choice без вариантов ответа: {len(choice_questions)}")
        for i, q in enumerate(choice_questions[:5], 1):  # Показываем первые 5
            text_preview = q['text'][:80] + "..." if len(q['text']) > 80 else q['text']
            print(f"  {i}. ID {q['id']} [{q['type']}]: {text_preview}")

        if len(choice_questions) > 5:
            print(f"  ... и ещё {len(choice_questions) - 5} вопросов")
        print()

    if matching_questions:
        print(f"📝 Вопросы matching без пар соответствия: {len(matching_questions)}")
        for i, q in enumerate(matching_questions[:5], 1):  # Показываем первые 5
            text_preview = q['text'][:80] + "..." if len(q['text']) > 80 else q['text']
            print(f"  {i}. ID {q['id']} [{q['type']}]: {text_preview}")

        if len(matching_questions) > 5:
            print(f"  ... и ещё {len(matching_questions) - 5} вопросов")
        print()

    return True


def delete_invalid_questions(db_path: str, choice_questions, matching_questions):
    """Удалить невалидные вопросы"""
    all_ids = [q['id'] for q in choice_questions] + [q['id'] for q in matching_questions]

    if not all_ids:
        return 0

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    try:
        # Удаляем все невалидные вопросы
        placeholders = ','.join(['?'] * len(all_ids))
        cursor.execute(f"""
            DELETE FROM questions
            WHERE id IN ({placeholders})
        """, all_ids)

        deleted_count = cursor.rowcount
        conn.commit()

        print(f"✅ Удалено {deleted_count} невалидных вопросов")

        return deleted_count

    except Exception as e:
        conn.rollback()
        print(f"❌ Ошибка при удалении: {e}")
        return 0

    finally:
        conn.close()


def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description='Удаление вопросов без вариантов ответа')
    parser.add_argument('--confirm', action='store_true',
                        help='Автоматически подтвердить удаление без запроса')
    parser.add_argument('--db', default='olympiad_questions.db',
                        help='Путь к базе данных (по умолчанию: olympiad_questions.db)')

    args = parser.parse_args()
    db_path = args.db

    if not Path(db_path).exists():
        print(f"❌ База данных не найдена: {db_path}")
        return

    # Находим невалидные вопросы
    choice_questions, matching_questions = find_invalid_questions(db_path)

    # Показываем найденные вопросы
    has_invalid = display_invalid_questions(choice_questions, matching_questions)

    if not has_invalid:
        return

    # Запрашиваем подтверждение
    if args.confirm:
        print("\n✅ Автоматическое подтверждение (--confirm)")
        should_delete = True
    else:
        print("\n⚠️  ВНИМАНИЕ: Эти вопросы будут безвозвратно удалены!")
        response = input("Продолжить удаление? (yes/no): ").strip().lower()
        should_delete = response in ['yes', 'y', 'да', 'д']

    if should_delete:
        deleted = delete_invalid_questions(db_path, choice_questions, matching_questions)
        print(f"\n✅ Очистка завершена. Удалено записей: {deleted}")
    else:
        print("\n❌ Отменено пользователем")


if __name__ == "__main__":
    main()
