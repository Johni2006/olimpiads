-- Добавление поля correct_text для текстовых вопросов
-- Это поле используется для хранения правильного ответа на текстовые вопросы

ALTER TABLE questions ADD COLUMN correct_text TEXT DEFAULT NULL;
