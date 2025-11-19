"""
Сервис для работы с Google Gemini API
"""
import os
import json
from typing import Optional, Dict, Any
import google.generativeai as genai


class GeminiService:
    """Сервис для анализа эссе и викторин с помощью Gemini AI"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Инициализация сервиса Gemini

        Args:
            api_key: API ключ Google Gemini (если не указан, берется из переменной окружения)
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')

        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY не найден. Установите переменную окружения или передайте api_key"
            )

        # Конфигурируем Gemini
        genai.configure(api_key=self.api_key)

        # Используем модель Gemini 2.5 Flash (стабильная версия, быстрая и эффективная)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

        # Настройки генерации
        self.generation_config = {
            'temperature': 0.7,  # Творческость (0-1)
            'top_p': 0.8,
            'top_k': 40,
            'max_output_tokens': 2048,
        }

        # Настройки безопасности (пропускаем образовательный контент)
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
        ]

    def analyze_essay(
        self,
        question_text: str,
        student_answer: str,
        guidelines: Optional[str] = None,
        prompt_template: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Анализ эссе студента

        Args:
            question_text: Текст вопроса
            student_answer: Ответ студента
            guidelines: Рекомендации преподавателя
            prompt_template: Шаблон промпта (если None, используется стандартный)

        Returns:
            Dict с результатом анализа и метаданными
        """
        # Используем шаблон промпта или стандартный
        if not prompt_template:
            prompt_template = """Проанализируй ответ ученика на вопрос.

Вопрос: {question_text}
Ответ ученика: {student_answer}
Рекомендации преподавателя: {guidelines}

Оцени ответ по следующим критериям:
1. Полнота ответа
2. Грамотность изложения
3. Логическая структура
4. Соответствие теме

Дай конструктивную обратную связь и рекомендации для улучшения."""

        # Форматируем промпт
        prompt = prompt_template.format(
            question_text=question_text,
            student_answer=student_answer,
            guidelines=guidelines or "Нет дополнительных рекомендаций"
        )

        try:
            # Генерируем ответ
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )

            return {
                'success': True,
                'feedback': response.text,
                'prompt_tokens': response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else None,
                'completion_tokens': response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else None,
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'feedback': None
            }

    def analyze_quiz(
        self,
        quiz_name: str,
        total_score: float,
        max_score: float,
        questions_data: list,
        prompt_template: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Общий анализ прохождения викторины

        Args:
            quiz_name: Название викторины
            total_score: Набранные баллы
            max_score: Максимальные баллы
            questions_data: Список вопросов с ответами
            prompt_template: Шаблон промпта

        Returns:
            Dict с результатом анализа
        """
        # Рассчитываем процент
        percentage = (total_score / max_score * 100) if max_score > 0 else 0

        # Форматируем данные о вопросах
        questions_summary = []
        for i, q in enumerate(questions_data, 1):
            questions_summary.append(
                f"{i}. {q.get('question_text', 'Вопрос без текста')}\n"
                f"   Ответ: {'✓ Правильно' if q.get('is_correct') else '✗ Неправильно'}\n"
                f"   Баллы: {q.get('points_earned', 0)}/{q.get('points_total', 0)}"
            )

        questions_text = "\n\n".join(questions_summary)

        # Используем шаблон или стандартный промпт
        if not prompt_template:
            prompt_template = """Проанализируй результаты прохождения викторины учеником.

Название викторины: {quiz_name}
Результат: {total_score} из {max_score} баллов ({percentage}%)

Детали по вопросам:
{questions_data}

Проанализируй:
1. Общую успеваемость
2. Сильные стороны
3. Темы, требующие дополнительного изучения
4. Рекомендации для дальнейшего обучения

Дай мотивирующую и конструктивную обратную связь."""

        # Форматируем промпт
        prompt = prompt_template.format(
            quiz_name=quiz_name,
            total_score=total_score,
            max_score=max_score,
            percentage=f"{percentage:.1f}",
            questions_data=questions_text
        )

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )

            return {
                'success': True,
                'feedback': response.text,
                'prompt_tokens': response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else None,
                'completion_tokens': response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else None,
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'feedback': None
            }

    def test_connection(self) -> bool:
        """
        Тестирование подключения к Gemini API

        Returns:
            True если подключение успешно
        """
        try:
            response = self.model.generate_content("Скажи 'привет' на русском языке")
            return response.text is not None
        except Exception as e:
            print(f"Ошибка подключения к Gemini: {e}")
            return False


# Пример использования
if __name__ == "__main__":
    # Для тестирования нужно установить переменную окружения GEMINI_API_KEY
    try:
        service = GeminiService()

        # Тест подключения
        if service.test_connection():
            print("✅ Подключение к Gemini успешно!")

            # Тест анализа эссе
            result = service.analyze_essay(
                question_text="Что такое демократия?",
                student_answer="Демократия - это форма правления, где власть принадлежит народу.",
                guidelines="Ответ должен включать основные принципы демократии"
            )

            if result['success']:
                print("\n📝 Анализ эссе:")
                print(result['feedback'])
            else:
                print(f"\n❌ Ошибка анализа: {result['error']}")
        else:
            print("❌ Не удалось подключиться к Gemini")

    except ValueError as e:
        print(f"❌ {e}")
        print("\nДля работы с Gemini установите переменную окружения:")
        print("export GEMINI_API_KEY='ваш-ключ-api'")
