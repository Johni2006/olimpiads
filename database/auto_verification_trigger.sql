-- Триггер для автоматического обновления статуса verification_status PDF файлов
-- на основе процента проверенных вопросов

-- Триггер который срабатывает при обновлении вопроса
CREATE TRIGGER IF NOT EXISTS auto_update_pdf_verification_status
AFTER UPDATE OF verified ON questions
WHEN NEW.source_pdf IS NOT NULL
BEGIN
    UPDATE pdf_files
    SET verification_status = (
        SELECT CASE
            -- Если процент проверенных < 30% - не проверено
            WHEN (CAST(SUM(CASE WHEN verified = 1 THEN 1 ELSE 0 END) AS REAL) / COUNT(*)) < 0.3 THEN 'not_verified'
            -- Если процент проверенных >= 80% - полностью проверено
            WHEN (CAST(SUM(CASE WHEN verified = 1 THEN 1 ELSE 0 END) AS REAL) / COUNT(*)) >= 0.8 THEN 'verified'
            -- Иначе - частично проверено
            ELSE 'partially_verified'
        END
        FROM questions
        WHERE source_pdf = NEW.source_pdf
    )
    WHERE file_path = NEW.source_pdf
    AND manual_verification_override = 0;  -- Обновляем только если не было ручного переопределения
END;

-- Пересчитаем текущие статусы для всех PDF
UPDATE pdf_files
SET verification_status = (
    SELECT CASE
        WHEN (CAST(SUM(CASE WHEN verified = 1 THEN 1 ELSE 0 END) AS REAL) / COUNT(*)) < 0.3 THEN 'not_verified'
        WHEN (CAST(SUM(CASE WHEN verified = 1 THEN 1 ELSE 0 END) AS REAL) / COUNT(*)) >= 0.8 THEN 'verified'
        ELSE 'partially_verified'
    END
    FROM questions
    WHERE source_pdf = pdf_files.file_path
)
WHERE manual_verification_override = 0
AND EXISTS (SELECT 1 FROM questions WHERE source_pdf = pdf_files.file_path);
