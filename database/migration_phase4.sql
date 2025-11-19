-- Миграция для Фазы 4: AI-интеграция с Gemini
-- Дата: 2025-11-19

-- Добавление AI-промптов в таблицу викторин
ALTER TABLE quizzes ADD COLUMN ai_essay_analysis_prompt TEXT;
ALTER TABLE quizzes ADD COLUMN ai_quiz_analysis_prompt TEXT;

-- Добавление AI-фидбэка в таблицу ответов (для эссе)
ALTER TABLE quiz_answers ADD COLUMN ai_essay_feedback TEXT;

-- Добавление общего AI-фидбэка в таблицу попыток
ALTER TABLE quiz_attempts ADD COLUMN ai_quiz_overall_feedback TEXT;

-- Промпты по умолчанию для эссе
UPDATE quizzes SET ai_essay_analysis_prompt = 'Проанализируй ответ ученика на вопрос.

Вопрос: {question_text}
Ответ ученика: {student_answer}
Рекомендации преподавателя: {guidelines}

Оцени ответ по следующим критериям:
1. Полнота ответа
2. Грамотность изложения
3. Логическая структура
4. Соответствие теме

Дай конструктивную обратную связь и рекомендации для улучшения.'
WHERE ai_essay_analysis_prompt IS NULL;

-- Промпт по умолчанию для анализа викторины
UPDATE quizzes SET ai_quiz_analysis_prompt = 'Проанализируй результаты прохождения викторины учеником.

Название викторины: {quiz_name}
Результат: {total_score} из {max_score} баллов ({percentage}%)

Детали по вопросам:
{questions_data}

Проанализируй:
1. Общую успеваемость
2. Сильные стороны
3. Темы, требующие дополнительного изучения
4. Рекомендации для дальнейшего обучения

Дай мотивирующую и конструктивную обратную связь.'
WHERE ai_quiz_analysis_prompt IS NULL;
