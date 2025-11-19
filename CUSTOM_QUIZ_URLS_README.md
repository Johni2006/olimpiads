# Кастомные URL и контроль доступа для викторин

## Обзор

Система позволяет создавать красивые постоянные ссылки для викторин и контролировать доступ по email адресам и доменам.

## Новые возможности

### 1. Кастомные URL (Custom Slugs)

Вместо автоматически генерируемого кода типа `?code=ABC123`, теперь можно создать читаемую ссылку:
- `/quiz.html?slug=olimpiada-2025`
- `/quiz.html?slug=math-final-test`

**Использование в API:**

```javascript
// Установить кастомный slug
PUT /api/quizzes/{quiz_id}/custom-slug
{
  "custom_slug": "olimpiada-2025"
}

// Получить викторину по slug
GET /api/quizzes/slug/{slug}

// Начать викторину по slug
POST /api/quizzes/{slug}/start-by-slug
{
  "student_name": "Иван Иванов",
  "student_email": "ivan@example.com"
}
```

### 2. Контроль доступа по Email

Можно ограничить доступ к викторине:
- По конкретным email адресам: `student@school.ru`
- По доменам: `@school.ru` (все email с этого домена)

**Настройка:**

1. Включить проверку email для викторины:
```javascript
PUT /api/quizzes/{quiz_id}
{
  "require_email_validation": true
}
```

2. Добавить email/домены в белый список:
```javascript
POST /api/quizzes/{quiz_id}/access-control
{
  "entry_type": "email",  // или "domain"
  "entry_value": "student@school.ru",  // или "@school.ru"
  "created_by": "Учитель",
  "notes": "Участник олимпиады"
}
```

3. Удалить из белого списка:
```javascript
DELETE /api/quizzes/{quiz_id}/access-control/{entry_id}
```

4. Получить весь белый список:
```javascript
GET /api/quizzes/{quiz_id}/access-control
```

5. Проверить доступ:
```javascript
POST /api/quizzes/{quiz_id}/check-access
{
  "email": "student@school.ru"
}
// Вернет: { "success": true, "has_access": true/false }
```

## Улучшенная навигация по вопросам

В интерфейсе прохождения викторины добавлен сайдбар с:
- Списком всех вопросов
- Индикацией отвеченных вопросов (зеленая галочка)
- Возможностью перейти к любому вопросу по клику
- Мобильной адаптацией (компактный вид на маленьких экранах)

## База данных

### Новые поля в таблице `quizzes`:
- `custom_slug` VARCHAR(100) - кастомный URL slug
- `require_email_validation` BOOLEAN - требуется ли проверка email

### Новая таблица `quiz_access_control`:
```sql
CREATE TABLE quiz_access_control (
    id INTEGER PRIMARY KEY,
    quiz_id INTEGER NOT NULL,
    entry_type VARCHAR(20) NOT NULL,  -- 'email' или 'domain'
    entry_value VARCHAR(200) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(200),
    notes TEXT,
    FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
);
```

## Примеры использования

### Создать публичную викторину с красивой ссылкой

```javascript
// 1. Создаем викторину
POST /api/quizzes
{
  "title": "Олимпиада по математике 2025",
  "description": "Финальный тур",
  ...
}

// 2. Устанавливаем кастомный URL
PUT /api/quizzes/123/custom-slug
{
  "custom_slug": "math-2025-final"
}

// 3. Делимся ссылкой: http://localhost:8000/quiz.html?slug=math-2025-final
```

### Викторина только для учеников конкретной школы

```javascript
// 1. Включаем проверку email
PUT /api/quizzes/123
{
  "require_email_validation": true
}

// 2. Добавляем домен школы в белый список
POST /api/quizzes/123/access-control
{
  "entry_type": "domain",
  "entry_value": "@school42.edu"
}

// Теперь доступ есть только у email с доменом @school42.edu
```

### Викторина для конкретных учеников

```javascript
// Добавляем конкретные email адреса
POST /api/quizzes/123/access-control
{
  "entry_type": "email",
  "entry_value": "ivan@gmail.com"
}

POST /api/quizzes/123/access-control
{
  "entry_type": "email",
  "entry_value": "maria@yahoo.com"
}
```

## Логика проверки доступа

1. Если `require_email_validation = false` → доступ разрешен всем
2. Если `require_email_validation = true`:
   - Если белый список пуст → доступ разрешен всем
   - Если белый список не пуст:
     - Проверяется точное совпадение email
     - Проверяется совпадение домена
     - Если не найдено → доступ запрещен

## Файлы для просмотра

- **БД миграция:** `migrate_custom_urls.py`
- **API эндпоинты:** `api/app.py` (строки 4263-4506)
- **Методы менеджера:** `database/quiz_manager.py` (строки 652-809)
- **UI викторины:** `web/quiz.html` (улучшенная навигация с сайдбаром)

## Тестирование

Для тестирования всех новых функций запустите:
```bash
# 1. Запустите API
python api/app.py

# 2. Откройте админку викторин
open http://localhost:8000/quizzes_admin.html

# 3. Создайте викторину, установите custom_slug и настройте доступ

# 4. Проверьте прохождение викторины
open http://localhost:8000/quiz.html?slug=your-custom-slug
```
