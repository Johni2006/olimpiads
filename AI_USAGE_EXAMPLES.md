# Примеры использования AI-анализа

## 🤖 Анализ эссе студента

### Пример 1: Базовый анализ

```bash
curl -X POST http://localhost:5001/api/ai/analyze-essay \
  -H "Content-Type: application/json" \
  -d '{
    "question_text": "Что такое фотосинтез?",
    "student_answer": "Фотосинтез - это процесс, при котором растения используют солнечный свет для производства энергии.",
    "guidelines": "Оцени полноту ответа и научную точность"
  }'
```

### Пример 2: Анализ существующего ответа из БД

```bash
curl -X POST http://localhost:5001/api/ai/analyze-essay \
  -H "Content-Type: application/json" \
  -d '{
    "answer_id": 123
  }'
```

## 📊 Общий анализ викторины

```bash
curl -X POST http://localhost:5001/api/ai/analyze-quiz \
  -H "Content-Type: application/json" \
  -d '{
    "attempt_id": 456
  }'
```

AI проанализирует всю викторину и даст:
- Общую оценку успеваемости
- Сильные стороны студента
- Темы, требующие дополнительного изучения
- Рекомендации для дальнейшего обучения

## ⚙️ Настройка AI-промптов для викторины

### Получить текущие промпты

```bash
curl http://localhost:5001/api/quizzes/1/ai-prompts
```

### Обновить промпты

```bash
curl -X PUT http://localhost:5001/api/quizzes/1/ai-prompts \
  -H "Content-Type: application/json" \
  -d '{
    "ai_essay_analysis_prompt": "Проанализируй ответ на вопрос по биологии:\n\nВопрос: {question_text}\nОтвет: {student_answer}\nРекомендации: {guidelines}\n\nДай оценку с точки зрения биологической точности.",
    "ai_quiz_analysis_prompt": "Викторина: {quiz_name}\nРезультат: {total_score}/{max_score} ({percentage}%)\n\nДетали:\n{questions_data}\n\nДай мотивирующую обратную связь."
  }'
```

## 🔗 Интеграция с системой приглашений

### Workflow: Создать приглашение → Студент проходит → AI анализирует

```python
import requests

API = "http://localhost:5001/api"

# 1. Создаем приглашение
invitation = requests.post(f"{API}/quizzes/1/invitations", json={
    "student_name": "Иван Иванов",
    "student_email": "ivan@example.com",
    "created_by": "Учитель Петров"
}).json()

print(f"Отправь студенту: {invitation['link']}")

# 2. Студент проходит викторину по ссылке...
# После завершения получаем attempt_id

# 3. Анализируем результаты с AI
analysis = requests.post(f"{API}/ai/analyze-quiz", json={
    "attempt_id": 123  # ID попытки
}).json()

print("AI-анализ:", analysis['feedback'])

# 4. Добавляем заметку преподавателя
requests.post(f"{API}/attempts/123/notes", json={
    "note_text": f"AI-анализ: {analysis['feedback'][:200]}...",
    "note_type": "general",
    "teacher_name": "Учитель Петров",
    "is_private": False
})
```

## 📝 Python-библиотека для удобства

```python
# Создайте файл aditi_client.py

import requests
from typing import Optional, Dict, Any

class AditiClient:
    """Клиент для работы с Aditi Quiz API"""

    def __init__(self, base_url: str = "http://localhost:5001/api"):
        self.base_url = base_url

    def create_invitation(
        self,
        quiz_id: int,
        student_name: str,
        student_email: Optional[str] = None,
        created_by: str = "Teacher"
    ) -> Dict[str, Any]:
        """Создать персональное приглашение"""
        response = requests.post(
            f"{self.base_url}/quizzes/{quiz_id}/invitations",
            json={
                "student_name": student_name,
                "student_email": student_email,
                "created_by": created_by
            }
        )
        return response.json()

    def analyze_essay(
        self,
        answer_id: Optional[int] = None,
        question_text: Optional[str] = None,
        student_answer: Optional[str] = None,
        guidelines: Optional[str] = None
    ) -> Dict[str, Any]:
        """Анализ эссе с AI"""
        data = {}
        if answer_id:
            data["answer_id"] = answer_id
        else:
            data.update({
                "question_text": question_text,
                "student_answer": student_answer,
                "guidelines": guidelines
            })

        response = requests.post(
            f"{self.base_url}/ai/analyze-essay",
            json=data
        )
        return response.json()

    def analyze_quiz(self, attempt_id: int) -> Dict[str, Any]:
        """Общий анализ викторины"""
        response = requests.post(
            f"{self.base_url}/ai/analyze-quiz",
            json={"attempt_id": attempt_id}
        )
        return response.json()

    def add_teacher_note(
        self,
        attempt_id: int,
        note_text: str,
        teacher_name: str,
        note_type: str = "general",
        is_private: bool = False
    ) -> Dict[str, Any]:
        """Добавить заметку преподавателя"""
        response = requests.post(
            f"{self.base_url}/attempts/{attempt_id}/notes",
            json={
                "note_text": note_text,
                "teacher_name": teacher_name,
                "note_type": note_type,
                "is_private": is_private
            }
        )
        return response.json()

# Использование:
client = AditiClient()

# Создать приглашение
inv = client.create_invitation(1, "Мария Смирнова", "maria@example.com")
print(f"Ссылка: {inv['link']}")

# Анализировать эссе
feedback = client.analyze_essay(answer_id=123)
print(f"AI фидбэк: {feedback['feedback']}")

# Добавить заметку
client.add_teacher_note(
    attempt_id=123,
    note_text="Отличная работа!",
    teacher_name="Петров И.И.",
    note_type="strength"
)
```

## 🎓 Сценарий использования для преподавателя

### Шаг 1: Отправка викторины студентам

```python
client = AditiClient()

students = [
    {"name": "Иван Иванов", "email": "ivan@school.ru"},
    {"name": "Мария Петрова", "email": "maria@school.ru"},
    {"name": "Петр Сидоров", "email": "petr@school.ru"}
]

quiz_id = 5  # ID викторины по биологии

for student in students:
    invitation = client.create_invitation(
        quiz_id=quiz_id,
        student_name=student["name"],
        student_email=student["email"],
        created_by="Биология - Иванова А.А."
    )

    # Отправить email/Telegram
    send_message(student["email"], f"Привет! Пройди викторину: {invitation['link']}")
```

### Шаг 2: Автоматический анализ после завершения

```python
# После того как студент завершил викторину (attempt_id = 789)

# AI анализирует результаты
analysis = client.analyze_quiz(attempt_id=789)

# Сохраняем AI-фидбэк как заметку
client.add_teacher_note(
    attempt_id=789,
    note_text=f"🤖 AI-анализ:\n\n{analysis['feedback']}",
    teacher_name="AI Assistant",
    note_type="general",
    is_private=False  # Видно студенту
)

# Преподаватель добавляет свою заметку
client.add_teacher_note(
    attempt_id=789,
    note_text="Молодец! Обрати внимание на вопросы 3 и 7.",
    teacher_name="Иванова А.А.",
    note_type="recommendation",
    is_private=False
)
```

## 🚀 Запуск API сервера

```bash
cd /Users/evgenij/ashram/aditi
source venv/bin/activate
python api/app.py
```

API будет доступен на `http://localhost:5001`

## 📚 Полезные ссылки

- **Dashboard учеников:** http://localhost:5001/students.html
- **Профиль ученика:** http://localhost:5001/student_profile.html?name=ИмяУченика
- **Главная викторин:** http://localhost:5001/quizzes.html
- **API Health Check:** http://localhost:5001/api/health

---

**Создано:** 19 ноября 2025
**Модель AI:** Gemini 2.5 Flash
