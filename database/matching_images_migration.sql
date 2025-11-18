-- Миграция: добавление поддержки изображений для пар соответствия
-- Создано: 2025-11-18

-- Добавляем поле matching_pair_id в таблицу images для связи с парами соответствия
ALTER TABLE images ADD COLUMN matching_pair_id INTEGER REFERENCES matching_pairs(id) ON DELETE CASCADE;

-- Добавляем поле side для указания, к какой части пары относится изображение ('left' или 'right')
ALTER TABLE images ADD COLUMN matching_side VARCHAR(10);

-- Создаем индекс для быстрого поиска изображений по matching_pair_id
CREATE INDEX IF NOT EXISTS idx_images_matching_pair ON images(matching_pair_id);
