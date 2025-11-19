#!/usr/bin/env python3
"""
Тестирование AI-функционала Gemini
"""
import requests
import json

API_URL = "http://localhost:5001/api"

def test_essay_analysis():
    """Тест анализа эссе"""
    print("📝 Тестируем анализ эссе...")

    response = requests.post(f"{API_URL}/ai/analyze-essay", json={
        "question_text": "Что такое фотосинтез?",
        "student_answer": """Фотосинтез - это процесс, при котором растения
        используют солнечный свет для производства энергии. Они поглощают
        углекислый газ и воду, и в результате выделяют кислород.""",
        "guidelines": "Оцени полноту ответа, научную точность и структуру изложения"
    })

    if response.status_code == 200:
        result = response.json()
        print("✅ Анализ эссе успешен!")
        print("\nРезультат анализа:")
        print("-" * 60)
        print(result.get('feedback', 'Нет фидбэка'))
        print("-" * 60)
        return True
    else:
        print(f"❌ Ошибка: {response.status_code}")
        print(response.text)
        return False

def test_health_check():
    """Проверка доступности API"""
    print("🏥 Проверяем доступность API...")
    response = requests.get(f"{API_URL}/health")

    if response.status_code == 200:
        print("✅ API доступен")
        return True
    else:
        print("❌ API недоступен")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 ТЕСТИРОВАНИЕ GEMINI AI ИНТЕГРАЦИИ")
    print("=" * 60)
    print()

    # Проверяем доступность API
    if not test_health_check():
        print("\n❌ API недоступен. Убедитесь, что сервер запущен.")
        exit(1)

    print()

    # Тестируем анализ эссе
    if test_essay_analysis():
        print("\n🎉 Все тесты прошли успешно!")
    else:
        print("\n❌ Тест не пройден")
