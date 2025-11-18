-- Триггеры для валидации вопросов
-- Предотвращают создание и редактирование вопросов без вариантов ответа

-- ============================================================
-- Триггер 1: Предотвращает удаление последнего варианта ответа
-- для вопросов типа 'choice' или 'multiple_choice'
-- ============================================================

DROP TRIGGER IF EXISTS prevent_delete_last_option;

CREATE TRIGGER prevent_delete_last_option
BEFORE DELETE ON options
FOR EACH ROW
BEGIN
    -- Проверяем, является ли этот вариант последним для вопроса типа choice/multiple_choice
    SELECT CASE
        WHEN (
            SELECT type FROM questions WHERE id = OLD.question_id
        ) IN ('choice', 'multiple_choice')
        AND (
            SELECT COUNT(*) FROM options WHERE question_id = OLD.question_id
        ) = 1
        THEN RAISE(ABORT, 'Нельзя удалить последний вариант ответа для вопроса типа choice/multiple_choice')
    END;
END;


-- ============================================================
-- Триггер 2: Предотвращает удаление последней пары соответствия
-- для вопросов типа 'matching'
-- ============================================================

DROP TRIGGER IF EXISTS prevent_delete_last_matching_pair;

CREATE TRIGGER prevent_delete_last_matching_pair
BEFORE DELETE ON matching_pairs
FOR EACH ROW
BEGIN
    -- Проверяем, является ли эта пара последней для вопроса типа matching
    SELECT CASE
        WHEN (
            SELECT type FROM questions WHERE id = OLD.question_id
        ) = 'matching'
        AND (
            SELECT COUNT(*) FROM matching_pairs WHERE question_id = OLD.question_id
        ) = 1
        THEN RAISE(ABORT, 'Нельзя удалить последнюю пару соответствия для вопроса типа matching')
    END;
END;


-- ============================================================
-- Триггер 3: Проверяет наличие вариантов при изменении типа вопроса
-- на 'choice' или 'multiple_choice'
-- ============================================================

DROP TRIGGER IF EXISTS validate_question_type_change;

CREATE TRIGGER validate_question_type_change
BEFORE UPDATE OF type ON questions
FOR EACH ROW
WHEN NEW.type IN ('choice', 'multiple_choice') AND OLD.type NOT IN ('choice', 'multiple_choice')
BEGIN
    -- Проверяем, есть ли варианты ответа
    SELECT CASE
        WHEN (SELECT COUNT(*) FROM options WHERE question_id = NEW.id) = 0
        THEN RAISE(ABORT, 'Нельзя изменить тип вопроса на choice/multiple_choice без вариантов ответа')
    END;
END;


-- ============================================================
-- Триггер 4: Проверяет наличие пар при изменении типа вопроса
-- на 'matching'
-- ============================================================

DROP TRIGGER IF EXISTS validate_matching_type_change;

CREATE TRIGGER validate_matching_type_change
BEFORE UPDATE OF type ON questions
FOR EACH ROW
WHEN NEW.type = 'matching' AND OLD.type != 'matching'
BEGIN
    -- Проверяем, есть ли пары соответствия
    SELECT CASE
        WHEN (SELECT COUNT(*) FROM matching_pairs WHERE question_id = NEW.id) = 0
        THEN RAISE(ABORT, 'Нельзя изменить тип вопроса на matching без пар соответствия')
    END;
END;


-- ============================================================
-- Примечание:
-- Триггеры в SQLite не могут предотвратить INSERT в таблицу questions
-- без последующего INSERT в options/matching_pairs, так как они
-- выполняются в разных транзакциях.
--
-- Поэтому валидация при создании вопроса должна быть реализована
-- на уровне приложения (в db_manager.py и в web-интерфейсе).
-- ============================================================
