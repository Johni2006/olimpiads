# Фазы 3 и 4: Dashboard учеников и AI-интеграция

## 📋 Обзор

Этот документ описывает функционал Фаз 3 и 4 системы обучения:
- **Фаза 3**: Dashboard учеников с детальной статистикой, заметками и тегами
- **Фаза 4**: AI-анализ эссе и викторин с помощью Google Gemini
- **Система приглашений**: Персональные одноразовые ссылки для учеников

---

## 🎯 Фаза 3: Dashboard учеников

### Функционал

#### 1. Dashboard учеников (`/web/students.html`)
- Список всех учеников с статистикой
- Поиск по имени или email
- Сортировка по различным критериям:
  - Последняя активность
  - Средний балл
  - Количество викторин
  - Количество попыток
- Пагинация результатов
- Карточки с общей статистикой

#### 2. Профиль ученика (`/web/student_profile.html`)
- Детальная статистика по ученику:
  - Всего викторин пройдено
  - Всего попыток
  - Завершено попыток
  - Средний балл
- История всех попыток с результатами
- Заметки преподавателя для каждой попытки
- Теги для категоризации попыток

#### 3. Система заметок преподавателя
Преподаватель может добавлять заметки к каждой попытке:
- **Типы заметок:**
  - Общая заметка
  - Сильная сторона
  - Требует внимания
  - Рекомендация
- **Приватные заметки**: не показываются ученику
- **История заметок**: все заметки сохраняются

#### 4. Теги попыток
Система тегов для быстрой категоризации:
- Цветные теги (синий, зеленый, красный, желтый)
- Примеры: "требуется помощь", "отличный результат", "повторить тему"
- Быстрая фильтрация по тегам

### API эндпоинты Фазы 3

```
GET  /api/students                      - Список учеников с фильтрацией
GET  /api/students/<name>               - Профиль ученика
GET  /api/students/<name>/attempts      - Попытки ученика

GET  /api/attempts/<id>/notes           - Получить заметки попытки
POST /api/attempts/<id>/notes           - Добавить заметку
PUT  /api/notes/<id>                    - Обновить заметку
DELETE /api/notes/<id>                  - Удалить заметку

GET  /api/attempts/<id>/tags            - Получить теги попытки
POST /api/attempts/<id>/tags            - Добавить тег
DELETE /api/attempt-tags/<id>           - Удалить тег
```

---

## 🤖 Фаза 4: AI-интеграция с Gemini

### Настройка

1. **Получите API ключ Google Gemini:**
   - Перейдите на https://makersuite.google.com/app/apikey
   - Создайте новый API ключ

2. **Создайте файл `.env` в корне проекта:**
   ```bash
   GEMINI_API_KEY=ваш_api_ключ_здесь
   ```

3. **Установите зависимости:**
   ```bash
   source venv/bin/activate
   pip install google-generativeai grpcio grpcio-status
   ```

### Функционал

#### 1. Анализ эссе
AI анализирует текстовые ответы студентов по критериям:
- Полнота ответа
- Грамотность изложения
- Логическая структура
- Соответствие теме

**Использование:**
```bash
POST /api/ai/analyze-essay
{
  "answer_id": 123,  # ID ответа из quiz_answers
  # ИЛИ
  "question_text": "Текст вопроса",
  "student_answer": "Ответ студента",
  "guidelines": "Рекомендации преподавателя"
}
```

#### 2. Общий анализ викторины
AI анализирует всю викторину целиком:
- Общая успеваемость
- Сильные стороны
- Темы, требующие изучения
- Рекомендации

**Использование:**
```bash
POST /api/ai/analyze-quiz
{
  "attempt_id": 456  # ID попытки прохождения
}
```

#### 3. Настройка AI-промптов
Каждая викторина может иметь свои промпты для AI-анализа:

```bash
# Получить промпты
GET /api/quizzes/<quiz_id>/ai-prompts

# Обновить промпты
PUT /api/quizzes/<quiz_id>/ai-prompts
{
  "ai_essay_analysis_prompt": "Ваш кастомный промпт для эссе",
  "ai_quiz_analysis_prompt": "Ваш кастомный промпт для викторины"
}
```

**Плейсхолдеры в промптах:**
- Для эссе: `{question_text}`, `{student_answer}`, `{guidelines}`
- Для викторины: `{quiz_name}`, `{total_score}`, `{max_score}`, `{percentage}`, `{questions_data}`

### API эндпоинты Фазы 4

```
POST /api/ai/analyze-essay              - Анализ эссе с AI
POST /api/ai/analyze-quiz               - Общий анализ викторины
GET  /api/quizzes/<id>/ai-prompts       - Получить AI-промпты
PUT  /api/quizzes/<id>/ai-prompts       - Обновить AI-промпты
```

---

## 🔗 Система персональных приглашений

### Концепция
Вместо публичных кодов викторин, преподаватель создает персональные одноразовые ссылки для каждого ученика.

### Преимущества
- ✅ **Безопасность**: каждая ссылка одноразовая
- ✅ **Контроль**: видно кому и когда отправлена ссылка
- ✅ **Прозрачность**: нет анонимных прохождений
- ✅ **Telegram-ready**: легко интегрировать в бота
- ✅ **Срок действия**: можно установить дату истечения

### Использование

#### 1. Создать приглашение
```bash
POST /api/quizzes/<quiz_id>/invitations
{
  "student_name": "Иван Иванов",
  "student_email": "ivan@example.com",  # опционально
  "created_by": "Преподаватель",
  "expires_at": "2025-12-31T23:59:59",  # опционально
  "notes": "Заметка о приглашении"     # опционально
}

# Ответ:
{
  "success": true,
  "invitation": {...},
  "link": "http://localhost:3000/quiz.html?token=abc123xyz..."
}
```

#### 2. Отправить ссылку ученику
Отправьте полученную ссылку любым способом:
- Email
- Telegram
- WhatsApp
- SMS

#### 3. Ученик открывает ссылку
- Система проверяет токен
- Автоматически начинает викторину
- Ссылка становится использованной
- Старая ссылка больше не работает

#### 4. Управление приглашениями
```bash
# Все приглашения викторины
GET /api/quizzes/<quiz_id>/invitations

# Информация о приглашении
GET /api/quizzes/invitations/<token>

# Начать викторину по приглашению
POST /api/quizzes/invitations/<token>/start

# Удалить приглашение (только неиспользованное)
DELETE /api/invitations/<id>
```

### API эндпоинты приглашений

```
GET/POST /api/quizzes/<id>/invitations         - Приглашения викторины
GET      /api/quizzes/invitations/<token>      - Информация о приглашении
POST     /api/quizzes/invitations/<token>/start - Начать по приглашению
DELETE   /api/invitations/<id>                  - Удалить приглашение
```

---

## 📊 База данных

### Новые таблицы

#### teacher_notes
```sql
- id: INTEGER PRIMARY KEY
- attempt_id: INTEGER (ссылка на quiz_attempts)
- teacher_name: VARCHAR(200)
- note_text: TEXT
- note_type: VARCHAR(50) (general/strength/weakness/recommendation)
- is_private: BOOLEAN
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
```

#### attempt_tags
```sql
- id: INTEGER PRIMARY KEY
- attempt_id: INTEGER
- tag_name: VARCHAR(100)
- tag_color: VARCHAR(20)
- created_by: VARCHAR(200)
- created_at: TIMESTAMP
```

#### quiz_invitations
```sql
- id: INTEGER PRIMARY KEY
- quiz_id: INTEGER
- student_name: VARCHAR(200)
- student_email: VARCHAR(200)
- unique_token: VARCHAR(100) UNIQUE
- created_at: TIMESTAMP
- expires_at: TIMESTAMP
- is_used: BOOLEAN
- used_at: TIMESTAMP
- attempt_id: INTEGER
- created_by: VARCHAR(200)
- notes: TEXT
```

### Расширенные таблицы

#### quizzes (новые поля)
- `ai_essay_analysis_prompt`: TEXT - промпт для анализа эссе
- `ai_quiz_analysis_prompt`: TEXT - промпт для анализа викторины

#### quiz_answers (новые поля)
- `ai_essay_feedback`: TEXT - результат AI-анализа эссе

#### quiz_attempts (новые поля)
- `ai_quiz_overall_feedback`: TEXT - общий AI-фидбэк по викторине
- `invitation_id`: INTEGER - ссылка на приглашение

---

## 🚀 Запуск

### 1. Установка зависимостей
```bash
source venv/bin/activate
pip install -r requirements.txt
pip install google-generativeai grpcio grpcio-status
```

### 2. Применение миграций
```bash
python migrate_phase3.py    # Фаза 3: заметки и теги
python migrate_phase4.py    # Фаза 4: AI-промпты
python migrate_invitations.py  # Система приглашений
```

### 3. Настройка .env
Создайте файл `.env`:
```
GEMINI_API_KEY=ваш_ключ_api
```

### 4. Запуск сервера
```bash
python api/app.py
```

### 5. Открыть интерфейс
- Dashboard учеников: http://localhost:3000/students.html
- Профиль ученика: http://localhost:3000/student_profile.html?name=ИмяУченика

---

## 🔧 Примеры использования

### Создать приглашение и отправить ученику
```python
import requests

# Создать приглашение
response = requests.post('http://localhost:5001/api/quizzes/1/invitations', json={
    "student_name": "Иван Иванов",
    "student_email": "ivan@example.com",
    "created_by": "Учитель Петров"
})

data = response.json()
link = data['link']

# Отправить ссылку ученику (например, через Telegram бот)
send_telegram_message(student_id, f"Привет! Вот твоя викторина: {link}")
```

### Проанализировать эссе после прохождения
```python
# После того как ученик ответил на эссе-вопрос
response = requests.post('http://localhost:5001/api/ai/analyze-essay', json={
    "answer_id": 123  # ID ответа из БД
})

feedback = response.json()['feedback']
print(f"AI-фидбэк: {feedback}")
```

### Получить общий анализ викторины
```python
# После завершения викторины
response = requests.post('http://localhost:5001/api/ai/analyze-quiz', json={
    "attempt_id": 456  # ID попытки
})

overall_feedback = response.json()['feedback']
print(f"Общий AI-анализ: {overall_feedback}")
```

---

## 📝 Заметки для разработки

### Telegram бот (будущая интеграция)
Система приглашений идеально подходит для Telegram бота:

```python
# Пример интеграции
@bot.command('send_quiz')
async def send_quiz(ctx, student_id: int, quiz_id: int):
    # Создать приглашение
    invitation = create_invitation(quiz_id, get_student_name(student_id))

    # Отправить в Telegram
    await bot.send_message(student_id,
        f"Привет! Вот твоя викторина:\n{invitation['link']}")
```

### Безопасность
- ✅ API ключ Gemini в .env (не в коде!)
- ✅ .env в .gitignore
- ✅ Токены приглашений криптографически безопасные (secrets.token_urlsafe)
- ✅ Проверка срока действия приглашений
- ✅ Одноразовые приглашения

---

## 🎉 Итого реализовано

### Фаза 3 ✅ (ПОЛНОСТЬЮ РАБОТАЕТ)
- ✅ Dashboard учеников с поиском, сортировкой, пагинацией
- ✅ Профили учеников с детальной статистикой
- ✅ Система заметок преподавателя (4 типа заметок)
- ✅ Теги для попыток (цветные, настраиваемые)
- ✅ API для всего вышеперечисленного

### Фаза 4 ✅ (ПРОТЕСТИРОВАНО И РАБОТАЕТ)
- ✅ Google Gemini 2.5 Flash интеграция
- ✅ AI-анализ эссе (протестирован 19.11.2025)
- ✅ AI-анализ викторин
- ✅ Настраиваемые промпты для каждой викторины
- ✅ API для AI-функций
- ✅ Gemini сервис с обработкой ошибок
- ✅ Русскоязычные ответы AI
- ✅ Детальный анализ по критериям

### Система приглашений ✅ (ПОЛНОСТЬЮ РАБОТАЕТ)
- ✅ Персональные одноразовые ссылки
- ✅ Срок действия приглашений
- ✅ Отслеживание использования
- ✅ История приглашений
- ✅ API для управления приглашениями

---

## ✅ СТАТУС: ВСЕ ФАЗЫ ЗАВЕРШЕНЫ И ПРОТЕСТИРОВАНЫ

**Дата завершения:** 19 ноября 2025
**AI Модель:** Gemini 2.5 Flash (стабильная версия)
**Тестирование:** Пройдено успешно ✅

---

## 🔮 Что дальше?

### Рекомендуемые улучшения:
1. **UI для редактирования AI-промптов** в интерфейсе викторин
2. **Отображение AI-фидбэка** в профиле ученика
3. **Telegram бот** для автоматической отправки приглашений
4. **Email-уведомления** при создании приглашения
5. **Экспорт статистики** в PDF/Excel
6. **Графики прогресса** ученика (Chart.js)
7. **Групповые приглашения** (создать приглашения для группы учеников)

---

## 📚 Полезные ссылки

- [Google Gemini API](https://ai.google.dev/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)

---

**Автор**: Claude Code
**Дата**: 19 ноября 2025
**Версия**: 1.0
