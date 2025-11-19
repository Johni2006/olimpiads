-- Миграция для Фазы 3: Dashboard учеников и система заметок
-- Дата: 2025-11-19

-- Таблица заметок преподавателя о попытках прохождения викторин
CREATE TABLE IF NOT EXISTS teacher_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id INTEGER NOT NULL,
    teacher_name VARCHAR(200),
    note_text TEXT NOT NULL,
    note_type VARCHAR(50) DEFAULT 'general', -- 'general', 'strength', 'weakness', 'recommendation'
    is_private BOOLEAN DEFAULT 0, -- приватная заметка (не показывать ученику)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (attempt_id) REFERENCES quiz_attempts(id) ON DELETE CASCADE
);

-- Таблица тегов для попыток (например: "требуется помощь", "отличный результат")
CREATE TABLE IF NOT EXISTS attempt_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id INTEGER NOT NULL,
    tag_name VARCHAR(100) NOT NULL,
    tag_color VARCHAR(20) DEFAULT 'blue', -- цвет тега для UI
    created_by VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (attempt_id) REFERENCES quiz_attempts(id) ON DELETE CASCADE
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_teacher_notes_attempt ON teacher_notes(attempt_id);
CREATE INDEX IF NOT EXISTS idx_teacher_notes_teacher ON teacher_notes(teacher_name);
CREATE INDEX IF NOT EXISTS idx_attempt_tags_attempt ON attempt_tags(attempt_id);
CREATE INDEX IF NOT EXISTS idx_attempt_tags_name ON attempt_tags(tag_name);

-- Индекс для поиска учеников по имени
CREATE INDEX IF NOT EXISTS idx_quiz_attempts_student ON quiz_attempts(student_name);

-- Представление для детальной статистики по ученикам
CREATE VIEW IF NOT EXISTS student_stats AS
SELECT
    qa.student_name,
    qa.student_email,
    COUNT(DISTINCT qa.quiz_id) as quizzes_taken,
    COUNT(qa.id) as total_attempts,
    COUNT(CASE WHEN qa.completed_at IS NOT NULL THEN 1 END) as completed_attempts,
    COUNT(CASE WHEN qa.is_passed = 1 THEN 1 END) as passed_attempts,
    AVG(CASE WHEN qa.completed_at IS NOT NULL THEN qa.score END) as avg_score,
    AVG(CASE WHEN qa.completed_at IS NOT NULL THEN qa.points_earned END) as avg_points,
    MAX(qa.started_at) as last_activity,
    MIN(qa.started_at) as first_activity,
    (SELECT COUNT(*) FROM teacher_notes tn WHERE tn.attempt_id IN (
        SELECT id FROM quiz_attempts WHERE student_name = qa.student_name
    )) as total_notes
FROM quiz_attempts qa
GROUP BY qa.student_name, qa.student_email;

-- Представление для детальной информации о попытках с заметками
CREATE VIEW IF NOT EXISTS attempt_details AS
SELECT
    qa.*,
    q.title as quiz_title,
    q.description as quiz_description,
    (SELECT COUNT(*) FROM teacher_notes WHERE attempt_id = qa.id) as notes_count,
    (SELECT GROUP_CONCAT(tag_name, ', ') FROM attempt_tags WHERE attempt_id = qa.id) as tags
FROM quiz_attempts qa
LEFT JOIN quizzes q ON qa.quiz_id = q.id;
