-- Миграция для системы персональных приглашений на викторины
-- Дата: 2025-11-19

-- Таблица приглашений на викторины
CREATE TABLE IF NOT EXISTS quiz_invitations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id INTEGER NOT NULL,
    student_name VARCHAR(200) NOT NULL,
    student_email VARCHAR(200),
    unique_token VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_used BOOLEAN DEFAULT 0,
    used_at TIMESTAMP,
    attempt_id INTEGER,
    created_by VARCHAR(200),
    notes TEXT,
    FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE,
    FOREIGN KEY (attempt_id) REFERENCES quiz_attempts(id) ON DELETE SET NULL
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_invitations_token ON quiz_invitations(unique_token);
CREATE INDEX IF NOT EXISTS idx_invitations_quiz ON quiz_invitations(quiz_id);
CREATE INDEX IF NOT EXISTS idx_invitations_student ON quiz_invitations(student_name);
CREATE INDEX IF NOT EXISTS idx_invitations_used ON quiz_invitations(is_used);

-- Добавляем связь с приглашением в таблицу попыток
ALTER TABLE quiz_attempts ADD COLUMN invitation_id INTEGER REFERENCES quiz_invitations(id);

-- Представление для удобного просмотра приглашений
CREATE VIEW IF NOT EXISTS invitation_details AS
SELECT
    qi.*,
    q.title as quiz_title,
    q.description as quiz_description,
    q.time_limit,
    qa.started_at as attempt_started_at,
    qa.completed_at as attempt_completed_at,
    qa.score as attempt_score,
    CASE
        WHEN qi.is_used = 1 THEN 'Использовано'
        WHEN qi.expires_at IS NOT NULL AND datetime(qi.expires_at) < datetime('now') THEN 'Истекло'
        ELSE 'Активно'
    END as status
FROM quiz_invitations qi
LEFT JOIN quizzes q ON qi.quiz_id = q.id
LEFT JOIN quiz_attempts qa ON qi.attempt_id = qa.id;
