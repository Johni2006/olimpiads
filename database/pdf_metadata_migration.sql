-- Миграция: добавление таблицы метаданных PDF файлов
-- Создано: 2025-11-11

-- Таблица для хранения метаданных PDF файлов
CREATE TABLE IF NOT EXISTS pdf_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL UNIQUE,              -- Реальный путь к файлу на диске
    display_name TEXT NOT NULL,                  -- Отображаемое имя в интерфейсе
    university TEXT,                             -- Университет/организатор
    olympiad TEXT,                               -- Название олимпиады
    year TEXT,                                   -- Год
    subject TEXT,                                -- Предмет
    is_manual BOOLEAN DEFAULT 0,                 -- Признак ручного создания (без файла)
    question_count INTEGER DEFAULT 0,            -- Количество вопросов в PDF
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_pdf_files_university ON pdf_files(university);
CREATE INDEX IF NOT EXISTS idx_pdf_files_olympiad ON pdf_files(olympiad);
CREATE INDEX IF NOT EXISTS idx_pdf_files_year ON pdf_files(year);
CREATE INDEX IF NOT EXISTS idx_pdf_files_subject ON pdf_files(subject);
CREATE INDEX IF NOT EXISTS idx_pdf_files_path ON pdf_files(file_path);

-- Триггер для обновления updated_at
CREATE TRIGGER IF NOT EXISTS update_pdf_files_timestamp
AFTER UPDATE ON pdf_files
BEGIN
    UPDATE pdf_files SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Заполнить таблицу существующими PDF из questions
INSERT OR IGNORE INTO pdf_files (file_path, display_name, question_count)
SELECT
    source_pdf,
    -- Извлекаем имя файла из пути (берем последнюю часть после /)
    CASE
        WHEN source_pdf LIKE '%/%' THEN
            replace(replace(replace(replace(replace(replace(
                source_pdf,
                rtrim(source_pdf, replace(source_pdf, '/', '')), ''
            ), '/', ''), '/', ''), '/', ''), '/', ''), '/', '')
        ELSE source_pdf
    END as display_name,
    COUNT(*) as question_count
FROM questions
WHERE source_pdf IS NOT NULL
GROUP BY source_pdf;

-- Обновить метаданные PDF из существующих тегов вопросов
UPDATE pdf_files
SET
    university = (
        SELECT t.value
        FROM questions q
        JOIN tags t ON q.id = t.question_id
        WHERE q.source_pdf = pdf_files.file_path
        AND t.category = 'university'
        LIMIT 1
    ),
    subject = (
        SELECT t.value
        FROM questions q
        JOIN tags t ON q.id = t.question_id
        WHERE q.source_pdf = pdf_files.file_path
        AND t.category = 'subject'
        LIMIT 1
    ),
    year = (
        SELECT t.value
        FROM questions q
        JOIN tags t ON q.id = t.question_id
        WHERE q.source_pdf = pdf_files.file_path
        AND t.category = 'year'
        LIMIT 1
    );
