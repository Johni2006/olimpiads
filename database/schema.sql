-- Схема базы данных для системы олимпиадных вопросов
-- SQLite database schema

-- Таблица вопросов
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    type VARCHAR(50) NOT NULL,  -- 'choice', 'multiple_choice', 'matching', 'text'
    difficulty INTEGER DEFAULT 1,  -- 1-5 (1=легко, 5=сложно)
    points REAL DEFAULT 1.0,
    explanation TEXT,  -- объяснение правильного ответа
    correct_text TEXT,  -- правильный текстовый ответ (для вопросов типа text/essay)
    source_pdf VARCHAR(500),
    page_number INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица вариантов ответов
CREATE TABLE IF NOT EXISTS options (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    is_correct BOOLEAN DEFAULT 0,
    position INTEGER DEFAULT 0,  -- порядок отображения
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
);

-- Таблица для вопросов на соответствие (пары)
CREATE TABLE IF NOT EXISTS matching_pairs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL,
    left_text TEXT NOT NULL,
    right_text TEXT NOT NULL,
    position INTEGER DEFAULT 0,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
);

-- Таблица изображений (для вопросов с графиками, схемами и т.д.)
CREATE TABLE IF NOT EXISTS images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER,
    option_id INTEGER,  -- NULL если изображение относится к вопросу, иначе к варианту ответа
    file_path VARCHAR(500) NOT NULL,  -- путь к файлу изображения
    image_type VARCHAR(50),  -- 'graph', 'diagram', 'photo', 'scheme', 'other'
    position INTEGER DEFAULT 0,  -- позиция в вопросе/варианте
    width INTEGER,  -- ширина изображения
    height INTEGER,  -- высота изображения
    description TEXT,  -- описание изображения (если есть)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    FOREIGN KEY (option_id) REFERENCES options(id) ON DELETE CASCADE
);

-- Таблица тегов и метаданных
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL,
    category VARCHAR(50) NOT NULL,  -- 'subject', 'university', 'year', 'topic', 'stage'
    value VARCHAR(200) NOT NULL,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
);

-- Таблица университетов/организаторов
CREATE TABLE IF NOT EXISTS organizers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL UNIQUE,
    short_name VARCHAR(50),
    website VARCHAR(500)
);

-- Таблица предметов
CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    parent_id INTEGER,  -- для иерархии предметов
    FOREIGN KEY (parent_id) REFERENCES subjects(id)
);

-- Таблица сессий тестирования (для сохранения результатов)
CREATE TABLE IF NOT EXISTS test_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name VARCHAR(200),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    total_questions INTEGER DEFAULT 0,
    correct_answers INTEGER DEFAULT 0,
    score REAL DEFAULT 0.0
);

-- Таблица ответов студентов
CREATE TABLE IF NOT EXISTS student_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    answer TEXT,  -- JSON с выбранными вариантами или текстом ответа
    is_correct BOOLEAN DEFAULT 0,
    answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES test_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(id)
);

-- Индексы для ускорения поиска
CREATE INDEX IF NOT EXISTS idx_questions_type ON questions(type);
CREATE INDEX IF NOT EXISTS idx_questions_difficulty ON questions(difficulty);
CREATE INDEX IF NOT EXISTS idx_options_question ON options(question_id);
CREATE INDEX IF NOT EXISTS idx_tags_question ON tags(question_id);
CREATE INDEX IF NOT EXISTS idx_tags_category ON tags(category);
CREATE INDEX IF NOT EXISTS idx_tags_value ON tags(value);
CREATE INDEX IF NOT EXISTS idx_matching_question ON matching_pairs(question_id);
CREATE INDEX IF NOT EXISTS idx_images_question ON images(question_id);
CREATE INDEX IF NOT EXISTS idx_images_option ON images(option_id);

-- Представление для быстрого поиска вопросов с тегами
CREATE VIEW IF NOT EXISTS questions_with_tags AS
SELECT
    q.id,
    q.text,
    q.type,
    q.difficulty,
    q.points,
    q.source_pdf,
    GROUP_CONCAT(CASE WHEN t.category = 'subject' THEN t.value END) as subjects,
    GROUP_CONCAT(CASE WHEN t.category = 'university' THEN t.value END) as universities,
    GROUP_CONCAT(CASE WHEN t.category = 'year' THEN t.value END) as years,
    GROUP_CONCAT(CASE WHEN t.category = 'topic' THEN t.value END) as topics,
    GROUP_CONCAT(CASE WHEN t.category = 'stage' THEN t.value END) as stages
FROM questions q
LEFT JOIN tags t ON q.id = t.question_id
GROUP BY q.id;

-- ==================== PDF ФАЙЛЫ ====================

-- Таблица для хранения метаданных PDF файлов
CREATE TABLE IF NOT EXISTS pdf_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    university TEXT,
    olympiad TEXT,
    year TEXT,
    subject TEXT,
    is_manual BOOLEAN DEFAULT 0,
    question_count INTEGER DEFAULT 0,
    file_type VARCHAR(50) DEFAULT 'pdf',
    difficulty INTEGER,
    file_hash VARCHAR(64),
    download_source TEXT,
    verification_status VARCHAR(50) DEFAULT 'not_verified',
    manual_verification_override BOOLEAN DEFAULT 0,
    last_parsed_at TIMESTAMP,
    parser_version VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pdf_files_university ON pdf_files(university);
CREATE INDEX IF NOT EXISTS idx_pdf_files_olympiad ON pdf_files(olympiad);
CREATE INDEX IF NOT EXISTS idx_pdf_files_year ON pdf_files(year);
CREATE INDEX IF NOT EXISTS idx_pdf_files_subject ON pdf_files(subject);
CREATE INDEX IF NOT EXISTS idx_pdf_files_path ON pdf_files(file_path);

-- ==================== ВИКТОРИНЫ ====================

-- Добавляем поля verified к questions (если еще нет)
-- ALTER TABLE questions ADD COLUMN verified BOOLEAN DEFAULT 0;
-- ALTER TABLE questions ADD COLUMN verified_at TIMESTAMP;
-- ALTER TABLE questions ADD COLUMN verified_by VARCHAR(200);

-- Таблица викторин/тестов
CREATE TABLE IF NOT EXISTS quizzes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(300) NOT NULL,
    description TEXT,
    unique_code VARCHAR(50) NOT NULL UNIQUE,
    created_by VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    time_limit INTEGER,
    show_correct_answers BOOLEAN DEFAULT 0,
    allow_review BOOLEAN DEFAULT 1,
    pass_threshold REAL DEFAULT 0.0,
    shuffle_questions BOOLEAN DEFAULT 0,
    shuffle_options BOOLEAN DEFAULT 0,
    max_attempts INTEGER DEFAULT 1,
    available_from TIMESTAMP,
    available_until TIMESTAMP
);

-- Таблица вопросов в викторине
CREATE TABLE IF NOT EXISTS quiz_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    position INTEGER DEFAULT 0,
    points_override REAL,
    FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
);

-- Таблица попыток прохождения викторин
CREATE TABLE IF NOT EXISTS quiz_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id INTEGER NOT NULL,
    student_name VARCHAR(200) NOT NULL,
    student_email VARCHAR(200),
    unique_session_id VARCHAR(100) NOT NULL UNIQUE,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    time_spent INTEGER,
    total_questions INTEGER DEFAULT 0,
    correct_answers INTEGER DEFAULT 0,
    score REAL DEFAULT 0.0,
    points_earned REAL DEFAULT 0.0,
    points_total REAL DEFAULT 0.0,
    is_passed BOOLEAN DEFAULT 0,
    ip_address VARCHAR(50),
    FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
);

-- Таблица ответов в викторинах
CREATE TABLE IF NOT EXISTS quiz_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    answer TEXT,
    is_correct BOOLEAN DEFAULT 0,
    points_earned REAL DEFAULT 0.0,
    time_spent INTEGER,
    answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (attempt_id) REFERENCES quiz_attempts(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(id)
);

-- Индексы для викторин
CREATE INDEX IF NOT EXISTS idx_quizzes_code ON quizzes(unique_code);
CREATE INDEX IF NOT EXISTS idx_quizzes_active ON quizzes(is_active);
CREATE INDEX IF NOT EXISTS idx_quiz_questions_quiz ON quiz_questions(quiz_id);
CREATE INDEX IF NOT EXISTS idx_quiz_questions_question ON quiz_questions(question_id);
CREATE INDEX IF NOT EXISTS idx_quiz_attempts_quiz ON quiz_attempts(quiz_id);
CREATE INDEX IF NOT EXISTS idx_quiz_attempts_session ON quiz_attempts(unique_session_id);
CREATE INDEX IF NOT EXISTS idx_quiz_answers_attempt ON quiz_answers(attempt_id);
CREATE INDEX IF NOT EXISTS idx_quiz_answers_question ON quiz_answers(question_id);

-- Представление для статистики викторин
CREATE VIEW IF NOT EXISTS quiz_stats AS
SELECT
    q.id,
    q.title,
    q.unique_code,
    q.created_at,
    q.is_active,
    COUNT(DISTINCT qa.id) as total_attempts,
    COUNT(DISTINCT CASE WHEN qa.completed_at IS NOT NULL THEN qa.id END) as completed_attempts,
    AVG(CASE WHEN qa.completed_at IS NOT NULL THEN qa.score END) as avg_score,
    COUNT(DISTINCT CASE WHEN qa.is_passed = 1 THEN qa.id END) as passed_count,
    (SELECT COUNT(*) FROM quiz_questions WHERE quiz_id = q.id) as question_count
FROM quizzes q
LEFT JOIN quiz_attempts qa ON q.id = qa.quiz_id
GROUP BY q.id;

-- ==================== ДАННЫЕ ====================

-- Вставка базовых предметов
INSERT OR IGNORE INTO subjects (name) VALUES
    ('Обществознание'),
    ('Философия'),
    ('Право'),
    ('Политология'),
    ('Социология'),
    ('Экономика'),
    ('История'),
    ('Религиоведение'),
    ('Финансовая грамотность'),
    ('Журналистика');

-- Вставка университетов
INSERT OR IGNORE INTO organizers (name, short_name, website) VALUES
    ('МГУ им. М.В. Ломоносова', 'МГУ', 'https://olymp.msu.ru'),
    ('Высшая школа экономики', 'ВШЭ', 'https://olymp.hse.ru'),
    ('Всероссийская олимпиада школьников', 'ВСОШ', 'https://vos.olimpiada.ru'),
    ('РАНХиГС', 'РАНХиГС', 'https://olymp.ranepa.ru'),
    ('Санкт-Петербургский государственный университет', 'СПбГУ', 'https://olymp.spbu.ru'),
    ('МГИМО', 'МГИМО', 'https://olymp.mgimo.ru');
