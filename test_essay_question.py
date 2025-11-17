#!/usr/bin/env python3
"""
Тестовый скрипт для создания вопроса типа "эссе"
Демонстрирует сохранение эссе с рекомендациями по оцениванию
"""
import sqlite3
import json

DB_PATH = "olympiad_questions.db"

def create_essay_question():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("📝 Создание тестового вопроса типа 'эссе'...")

    # Данные для вопроса-эссе
    essay_question = {
        "text": """Напишите эссе на тему: "Роль философии в современном мире"

В вашем эссе рассмотрите следующие аспекты:
1. Определение философии и её основные направления
2. Влияние философских идей на развитие общества
3. Актуальность философских вопросов в XXI веке
4. Ваше личное отношение к значению философии

Объём эссе: не менее 300 слов.""",

        "type": "essay",

        "difficulty": 4,

        "points": 10.0,

        "essay_guidelines": """КРИТЕРИИ ОЦЕНИВАНИЯ ЭССЕ (максимум 10 баллов):

1. СОДЕРЖАНИЕ (5 баллов):
   - Раскрытие всех четырёх аспектов темы (1.25 балла за каждый)
   - Глубина анализа и аргументация
   - Использование философских терминов и концепций

2. СТРУКТУРА И ЛОГИКА (2 балла):
   - Наличие введения, основной части и заключения
   - Логическая связность между абзацами
   - Последовательность изложения мыслей

3. ЯЗЫКОВОЕ ОФОРМЛЕНИЕ (2 балла):
   - Грамотность речи
   - Разнообразие лексики
   - Отсутствие речевых ошибок

4. ОРИГИНАЛЬНОСТЬ (1 балл):
   - Наличие собственной позиции
   - Творческий подход к раскрытию темы
   - Примеры из личного опыта

ПРИМЕЧАНИЯ:
- За эссе объёмом менее 250 слов снимается 2 балла
- За отсутствие любого из четырёх аспектов снимается 1.5 балла
- Плагиат = 0 баллов""",

        "source_pdf": "olympiads/manual/test_essay.pdf",

        "page_number": 1
    }

    # Вставка вопроса
    cursor.execute("""
        INSERT INTO questions (
            text, type, difficulty, points, essay_guidelines,
            source_pdf, page_number
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        essay_question['text'],
        essay_question['type'],
        essay_question['difficulty'],
        essay_question['points'],
        essay_question['essay_guidelines'],
        essay_question['source_pdf'],
        essay_question['page_number']
    ))

    question_id = cursor.lastrowid
    conn.commit()

    print(f"✅ Вопрос создан с ID: {question_id}")

    # Проверка сохранения
    cursor.execute("""
        SELECT id, text, type, difficulty, points, essay_guidelines
        FROM questions
        WHERE id = ?
    """, (question_id,))

    result = cursor.fetchone()

    print("\n📊 СОХРАНЁННЫЕ ДАННЫЕ:")
    print(f"ID: {result[0]}")
    print(f"Тип: {result[2]}")
    print(f"Сложность: {result[3]}")
    print(f"Баллы: {result[4]}")
    print(f"\nТекст вопроса:")
    print("=" * 60)
    print(result[1][:200] + "...")
    print("=" * 60)
    print(f"\nРекомендации по оцениванию:")
    print("=" * 60)
    print(result[5][:300] + "...")
    print("=" * 60)

    # Создадим еще один пример - эссе с изображением
    print("\n📝 Создание второго вопроса-эссе (с будущим изображением)...")

    essay_with_image = {
        "text": """Проанализируйте представленную философскую схему и напишите эссе о взаимосвязи основных философских категорий.

В эссе необходимо:
1. Описать элементы схемы
2. Объяснить связи между категориями
3. Привести примеры из истории философии
4. Высказать своё мнение о полноте представленной классификации

Объём: 250-400 слов.""",

        "type": "essay",

        "difficulty": 5,

        "points": 12.0,

        "essay_guidelines": """КРИТЕРИИ ОЦЕНИВАНИЯ (12 баллов):

1. Анализ схемы (4 балла)
2. Исторические примеры (3 балла)
3. Критическое мышление (3 балла)
4. Язык и стиль (2 балла)""",

        "source_pdf": "olympiads/manual/test_essay_with_image.pdf",
        "page_number": 2
    }

    cursor.execute("""
        INSERT INTO questions (
            text, type, difficulty, points, essay_guidelines,
            source_pdf, page_number
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        essay_with_image['text'],
        essay_with_image['type'],
        essay_with_image['difficulty'],
        essay_with_image['points'],
        essay_with_image['essay_guidelines'],
        essay_with_image['source_pdf'],
        essay_with_image['page_number']
    ))

    question_id_2 = cursor.lastrowid
    conn.commit()

    print(f"✅ Второй вопрос создан с ID: {question_id_2}")

    # Добавим запись об изображении (путь пока фиктивный)
    cursor.execute("""
        INSERT INTO images (
            question_id, file_path, image_type, position, description
        ) VALUES (?, ?, ?, ?, ?)
    """, (
        question_id_2,
        "question_images/philosophical_categories_diagram.png",
        "diagram",
        0,
        "Схема основных философских категорий"
    ))

    conn.commit()
    print("✅ Изображение добавлено к вопросу")

    # Итоговая статистика
    cursor.execute("""
        SELECT COUNT(*) FROM questions WHERE type = 'essay'
    """)
    essay_count = cursor.fetchone()[0]

    print(f"\n📊 Всего вопросов типа 'essay': {essay_count}")

    conn.close()

if __name__ == "__main__":
    create_essay_question()
