-- Миграция для добавления таблицы настроек
-- Таблица настроек приложения
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key VARCHAR(100) NOT NULL UNIQUE,
    value TEXT,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Добавляем настройку по умолчанию для учителя
INSERT OR IGNORE INTO settings (key, value, description) VALUES
    ('default_teacher_name', '', 'Имя учителя по умолчанию для викторин');

-- Создаем индекс для быстрого поиска по ключу
CREATE INDEX IF NOT EXISTS idx_settings_key ON settings(key);
