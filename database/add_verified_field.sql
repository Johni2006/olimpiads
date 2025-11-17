-- Миграция: добавление поля verified для отметки проверенных вопросов

ALTER TABLE questions ADD COLUMN verified BOOLEAN DEFAULT 0;
ALTER TABLE questions ADD COLUMN verified_at TIMESTAMP;
ALTER TABLE questions ADD COLUMN verified_by VARCHAR(200);

-- Индекс для быстрого поиска непроверенных вопросов
CREATE INDEX IF NOT EXISTS idx_questions_verified ON questions(verified);
