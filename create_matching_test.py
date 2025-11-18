#!/usr/bin/env python3
"""
Скрипт для создания тестового вопроса типа "Соответствие"
с возможностью добавления изображений
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from database.db_manager import DatabaseManager

def create_matching_question():
    """Создать тестовый вопрос на соответствие"""

    db = DatabaseManager('olympiad_questions.db')

    # Данные вопроса
    text = "Установите соответствие между животными и их средой обитания:"
    question_type = "matching"
    difficulty = 2
    points = 3.0
    tags = {
        "subject": ["Биология"],
        "university": ["МГУ"],
        "year": ["2024"]
    }
    matching_pairs = [
        ("Дельфин", "Океан"),
        ("Орёл", "Горы"),
        ("Верблюд", "Пустыня"),
        ("Белый медведь", "Арктика")
    ]

    try:
        # Создаем вопрос
        question_id = db.add_question(
            text=text,
            question_type=question_type,
            matching_pairs=matching_pairs,
            tags=tags,
            difficulty=difficulty,
            points=points
        )

        if question_id:
            print(f"✅ Тестовый вопрос на соответствие успешно создан!")
            print(f"   ID вопроса: {question_id}")
            print(f"   Текст: {text}")
            print(f"   Количество пар: {len(matching_pairs)}")
            print()
            print("📝 Пары соответствия:")
            for i, pair in enumerate(matching_pairs, 1):
                print(f"   {i}. {pair[0]} ↔ {pair[1]}")
            print()
            print("🖼️  Вы можете добавить изображения через веб-интерфейс:")
            print(f"   1. Откройте http://localhost:8080")
            print(f"   2. Перейдите в раздел 'Просмотр вопросов'")
            print(f"   3. Найдите вопрос #{question_id}")
            print(f"   4. Нажмите кнопку редактирования")
            print(f"   5. Используйте кнопки '🖼️ L' и '🖼️ R' для загрузки изображений")
            print()
            print("💡 Совет: Загрузите изображения дельфина, орла, верблюда и белого медведя")
            print("   для левой части, и изображения океана, гор, пустыни и арктики для правой!")

            return question_id
        else:
            print("❌ Ошибка при создании вопроса")
            return None

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

if __name__ == "__main__":
    create_matching_question()
