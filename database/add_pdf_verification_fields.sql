-- Добавление полей для верификации и расширенных метаданных PDF файлов

ALTER TABLE pdf_files ADD COLUMN file_type VARCHAR(50) DEFAULT 'pdf';
ALTER TABLE pdf_files ADD COLUMN difficulty INTEGER;
ALTER TABLE pdf_files ADD COLUMN file_hash VARCHAR(64);
ALTER TABLE pdf_files ADD COLUMN download_source TEXT;
ALTER TABLE pdf_files ADD COLUMN verification_status VARCHAR(50) DEFAULT 'not_verified';
ALTER TABLE pdf_files ADD COLUMN manual_verification_override BOOLEAN DEFAULT 0;
ALTER TABLE pdf_files ADD COLUMN last_parsed_at TIMESTAMP;
ALTER TABLE pdf_files ADD COLUMN parser_version VARCHAR(20);
