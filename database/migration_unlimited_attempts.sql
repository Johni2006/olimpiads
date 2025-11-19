-- Миграция для добавления поля unlimited_attempts в таблицу quizzes
-- Позволяет отключить ограничение на количество попыток

-- Добавляем поле unlimited_attempts
ALTER TABLE quizzes ADD COLUMN unlimited_attempts BOOLEAN DEFAULT 0;

-- Для существующих викторин: если max_attempts = 0, то включаем unlimited_attempts
UPDATE quizzes SET unlimited_attempts = 1 WHERE max_attempts = 0 OR max_attempts IS NULL;
