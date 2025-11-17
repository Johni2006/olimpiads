-- Дополнительные таблицы для системы викторин
-- Migration для добавления функционала викторин

-- Добавляем поля verified к questions (если еще нет)
ALTER TABLE questions ADD COLUMN verified BOOLEAN DEFAULT 0;
ALTER TABLE questions ADD COLUMN verified_at TIMESTAMP;
ALTER TABLE questions ADD COLUMN verified_by VARCHAR(200);

-- Таблица викторин/тестов
CREATE TABLE IF NOT EXISTS quizzes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(300) NOT NULL,
    description TEXT,
    unique_code VARCHAR(50) NOT NULL UNIQUE,  -- уникальный код для доступа
    created_by VARCHAR(200),  -- имя создателя (учителя)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,  -- активна ли викторина
    time_limit INTEGER,  -- лимит времени в минутах (NULL = без лимита)
    show_correct_answers BOOLEAN DEFAULT 0,  -- показывать ли правильные ответы после завершения
    allow_review BOOLEAN DEFAULT 1,  -- разрешить ли просмотр результатов
    pass_threshold REAL DEFAULT 0.0,  -- порог прохождения (0-100%)
    shuffle_questions BOOLEAN DEFAULT 0,  -- перемешивать вопросы
    shuffle_options BOOLEAN DEFAULT 0,  -- перемешивать варианты ответов
    max_attempts INTEGER DEFAULT 1,  -- максимальное количество попыток (NULL = без лимита)
    available_from TIMESTAMP,  -- доступна с
    available_until TIMESTAMP  -- доступна до
);

-- Таблица вопросов в викторине
CREATE TABLE IF NOT EXISTS quiz_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    position INTEGER DEFAULT 0,  -- порядок вопроса в викторине
    points_override REAL,  -- переопределить баллы за вопрос (NULL = использовать из questions)
    FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
);

-- Обновляем таблицу test_sessions для связи с викторинами
-- Сначала создадим новую таблицу
CREATE TABLE IF NOT EXISTS quiz_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id INTEGER NOT NULL,
    student_name VARCHAR(200) NOT NULL,
    student_email VARCHAR(200),  -- опционально
    unique_session_id VARCHAR(100) NOT NULL UNIQUE,  -- уникальный ID сессии
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    time_spent INTEGER,  -- время в секундах
    total_questions INTEGER DEFAULT 0,
    correct_answers INTEGER DEFAULT 0,
    score REAL DEFAULT 0.0,  -- процент правильных ответов
    points_earned REAL DEFAULT 0.0,  -- заработанные баллы
    points_total REAL DEFAULT 0.0,  -- максимальные баллы
    is_passed BOOLEAN DEFAULT 0,  -- прошел ли тест
    ip_address VARCHAR(50),  -- IP адрес студента
    FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
);

-- Обновляем таблицу ответов студентов
CREATE TABLE IF NOT EXISTS quiz_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    answer TEXT,  -- JSON с выбранными вариантами или текстом ответа
    is_correct BOOLEAN DEFAULT 0,
    points_earned REAL DEFAULT 0.0,
    time_spent INTEGER,  -- время на ответ в секундах
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
CREATE INDEX IF NOT EXISTS idx_questions_verified ON questions(verified);

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
