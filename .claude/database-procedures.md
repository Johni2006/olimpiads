# Инструкция по работе с базой данных

## КРИТИЧЕСКИ ВАЖНО: ВСЕГДА ЧИТАТЬ ПЕРЕД РАБОТОЙ С БД

Этот документ содержит правила работы с базой данных проекта. Несоблюдение этих правил приводит к потере данных и ошибкам.

---

## Структура базы данных

### Основные файлы
- `olympiad_questions.db` - файл базы данных SQLite
- `database/schema.sql` - ОСНОВНАЯ схема базы данных (полная)
- `database/*.sql` - миграционные файлы для добавления новых функций

### Миграционные файлы
- `settings_migration.sql` - добавляет таблицу настроек
- `add_verified_field.sql` - добавляет поля проверки вопросов
- `pdf_metadata_migration.sql` - расширяет метаданные PDF
- `add_pdf_verification_fields.sql` - добавляет поля верификации PDF
- `matching_images_migration.sql` - добавляет поддержку изображений для вопросов на соответствие
- `add_correct_text_field.sql` - добавляет поле для текстовых ответов
- `validation_triggers.sql` - добавляет триггеры валидации
- `auto_verification_trigger.sql` - добавляет триггер автоматической верификации

---

## ПРАВИЛО №1: НИКОГДА НЕ УДАЛЯТЬ БД БЕЗ БЭКАПА

### Перед удалением базы данных ВСЕГДА выполнить:

```bash
# 1. Создать бэкап с датой и временем
timestamp=$(date +%Y%m%d_%H%M%S)
cp olympiad_questions.db "backups/olympiad_questions_${timestamp}.db"

# 2. Экспортировать схему и данные
sqlite3 olympiad_questions.db .dump > "backups/backup_${timestamp}.sql"
```

### Если нужно пересоздать БД:

```bash
# 1. ОБЯЗАТЕЛЬНО сделать бэкап (см. выше)

# 2. Удалить старую БД
rm olympiad_questions.db

# 3. Создать новую БД с основной схемой
sqlite3 olympiad_questions.db < database/schema.sql

# 4. Применить ВСЕ необходимые миграции
sqlite3 olympiad_questions.db < database/settings_migration.sql
# Применить другие миграции по необходимости

# 5. Восстановить данные из бэкапа (если нужно)
sqlite3 olympiad_questions.db < backups/backup_TIMESTAMP.sql
```

---

## ПРАВИЛО №2: Новые изменения схемы

### Для НОВЫХ установок:
1. Добавить изменения в `database/schema.sql` (основная схема)
2. Создать миграционный файл `database/название_migration.sql` для существующих БД

### Для СУЩЕСТВУЮЩИХ БД:
1. Создать миграционный файл в `database/`
2. Применить миграцию: `sqlite3 olympiad_questions.db < database/новая_миграция.sql`
3. Обновить `database/schema.sql` чтобы новые установки получили эти изменения

---

## ПРАВИЛО №3: Проверка состояния БД

### Перед любой работой проверить:

```bash
# Проверить какие таблицы существуют
sqlite3 olympiad_questions.db "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"

# Проверить количество записей
sqlite3 olympiad_questions.db "SELECT
    (SELECT COUNT(*) FROM questions) as questions,
    (SELECT COUNT(*) FROM pdf_files) as pdfs,
    (SELECT COUNT(*) FROM quizzes) as quizzes;"
```

### Ожидаемые таблицы (минимум):
- questions
- options
- matching_pairs
- images
- tags
- organizers
- subjects
- test_sessions
- student_answers
- pdf_files
- quizzes
- quiz_questions
- quiz_attempts
- quiz_answers
- settings

Если таблиц меньше - БД повреждена или не полностью инициализирована!

---

## ПРАВИЛО №4: Восстановление после ошибок

### Если появляется "no such table":

```bash
# 1. Проверить какие таблицы существуют
sqlite3 olympiad_questions.db ".tables"

# 2. Если таблиц мало или нет вообще:
#    a) Проверить есть ли бэкап
ls -la backups/

#    b) Если бэкап есть:
mv olympiad_questions.db olympiad_questions_broken.db
sqlite3 olympiad_questions.db < database/schema.sql
sqlite3 olympiad_questions.db < database/settings_migration.sql
# Восстановить данные из последнего бэкапа

#    c) Если бэкапа нет:
rm olympiad_questions.db
sqlite3 olympiad_questions.db < database/schema.sql
sqlite3 olympiad_questions.db < database/settings_migration.sql
# Начать с чистой БД (данные потеряны!)
```

---

## ПРАВИЛО №5: Автоматические бэкапы

### Рекомендуется создать cronjob для автоматических бэкапов:

```bash
# Создать директорию для бэкапов
mkdir -p backups

# Добавить в crontab (каждый день в 3:00 AM):
0 3 * * * cd /path/to/aditi && timestamp=$(date +\%Y\%m\%d_\%H\%M\%S) && cp olympiad_questions.db "backups/auto_${timestamp}.db" && find backups/ -name "auto_*.db" -mtime +7 -delete
```

---

## ПРАВИЛО №6: При работе с миграциями

### ВСЕГДА:
1. Читать миграционный файл перед применением
2. Проверять что миграция не конфликтует с текущей схемой
3. Делать бэкап перед применением миграции
4. Тестировать на копии БД перед применением к продакшн

### НИКОГДА:
1. НЕ применять миграцию дважды
2. НЕ редактировать миграцию после применения
3. НЕ удалять миграционные файлы

---

## Быстрая проверка целостности

```bash
# Запустить эту команду для быстрой проверки
sqlite3 olympiad_questions.db "
SELECT
    'OK' as status,
    (SELECT COUNT(*) FROM sqlite_master WHERE type='table') as tables_count,
    (SELECT COUNT(*) FROM questions) as questions_count,
    (SELECT COUNT(*) FROM pdf_files) as pdfs_count,
    (SELECT COUNT(*) FROM quizzes) as quizzes_count;
"
```

Ожидаемые значения:
- tables_count >= 16
- questions_count, pdfs_count, quizzes_count >= 0

---

## Контакты и помощь

При любых проблемах с БД:
1. НЕ ПАНИКОВАТЬ
2. НЕ УДАЛЯТЬ НИЧЕГО
3. Проверить наличие бэкапа
4. Создать бэкап текущего состояния
5. Только потом принимать решения

---

**ПОМНИТЕ: Данные ценнее кода. Код можно переписать, данные - нет.**
