"""
Расширение DatabaseManager для работы с викторинами
"""
import secrets
import string
from typing import List, Dict, Optional
from datetime import datetime


def generate_unique_code(length: int = 8) -> str:
    """Генерировать уникальный код для викторины"""
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


class QuizManager:
    """Методы для работы с викторинами (примесь для DatabaseManager)"""

    # ==================== СОЗДАНИЕ И УПРАВЛЕНИЕ ВИКТОРИНАМИ ====================

    def create_quiz(
        self,
        title: str,
        description: str = None,
        created_by: str = None,
        question_ids: List[int] = None,
        status: str = 'draft',
        time_limit: int = None,
        show_correct_answers: bool = False,
        allow_review: bool = True,
        pass_threshold: float = 0.0,
        shuffle_questions: bool = False,
        shuffle_options: bool = False,
        max_attempts: int = 1,
        available_from: str = None,
        available_until: str = None
    ) -> Dict:
        """
        Создать новую викторину

        Args:
            title: Название викторины
            description: Описание
            created_by: Имя создателя
            question_ids: Список ID вопросов для викторины
            time_limit: Лимит времени в минутах
            show_correct_answers: Показывать ли правильные ответы после завершения
            allow_review: Разрешить ли просмотр результатов
            pass_threshold: Порог прохождения (0-100%)
            shuffle_questions: Перемешивать вопросы
            shuffle_options: Перемешивать варианты ответов
            max_attempts: Максимальное количество попыток
            available_from: Дата начала доступности
            available_until: Дата окончания доступности

        Returns:
            Словарь с данными созданной викторины
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Генерируем уникальный код
            unique_code = generate_unique_code()

            # Проверяем, что код действительно уникален
            cursor.execute("SELECT id FROM quizzes WHERE unique_code = ?", (unique_code,))
            while cursor.fetchone():
                unique_code = generate_unique_code()
                cursor.execute("SELECT id FROM quizzes WHERE unique_code = ?", (unique_code,))

            # Создаем викторину
            cursor.execute("""
                INSERT INTO quizzes (
                    title, description, unique_code, created_by, status,
                    time_limit, show_correct_answers, allow_review, pass_threshold,
                    shuffle_questions, shuffle_options, max_attempts,
                    available_from, available_until
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                title, description, unique_code, created_by, status,
                time_limit, show_correct_answers, allow_review, pass_threshold,
                shuffle_questions, shuffle_options, max_attempts,
                available_from, available_until
            ))

            quiz_id = cursor.lastrowid

            # Добавляем вопросы
            if question_ids:
                for position, question_id in enumerate(question_ids):
                    cursor.execute("""
                        INSERT INTO quiz_questions (quiz_id, question_id, position)
                        VALUES (?, ?, ?)
                    """, (quiz_id, question_id, position))

            conn.commit()  # Commit before reading

            # Получаем созданную викторину
            return self.get_quiz(quiz_id)

    def get_quiz(self, quiz_id: int = None, unique_code: str = None) -> Optional[Dict]:
        """Получить викторину по ID или уникальному коду"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            if quiz_id:
                cursor.execute("SELECT * FROM quizzes WHERE id = ?", (quiz_id,))
            elif unique_code:
                cursor.execute("SELECT * FROM quizzes WHERE unique_code = ?", (unique_code,))
            else:
                return None

            row = cursor.fetchone()
            if not row:
                return None

            quiz = dict(row)

            # Получаем вопросы викторины
            quiz['questions'] = self._get_quiz_questions(quiz['id'])
            quiz['question_count'] = len(quiz['questions'])

            # Получаем статистику
            cursor.execute("""
                SELECT
                    COUNT(*) as total_attempts,
                    COUNT(CASE WHEN completed_at IS NOT NULL THEN 1 END) as completed_attempts,
                    AVG(CASE WHEN completed_at IS NOT NULL THEN score END) as avg_score
                FROM quiz_attempts
                WHERE quiz_id = ?
            """, (quiz['id'],))

            stats = cursor.fetchone()
            quiz['stats'] = dict(stats) if stats else {
                'total_attempts': 0,
                'completed_attempts': 0,
                'avg_score': 0
            }

            return quiz

    def get_all_quizzes(
        self,
        created_by: str = None,
        is_active: bool = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """Получить список всех викторин"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM quiz_stats WHERE 1=1"
            params = []

            if created_by:
                query += " AND created_by = ?"
                params.append(created_by)

            if is_active is not None:
                query += " AND is_active = ?"
                params.append(1 if is_active else 0)

            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def update_quiz(self, quiz_id: int, data: Dict) -> bool:
        """Обновить викторину"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Проверяем существование викторины
            cursor.execute("SELECT id FROM quizzes WHERE id = ?", (quiz_id,))
            if not cursor.fetchone():
                return False

            # Обновляем поля
            update_fields = []
            params = []

            allowed_fields = [
                'title', 'description', 'is_active', 'status', 'time_limit',
                'show_correct_answers', 'allow_review', 'pass_threshold',
                'shuffle_questions', 'shuffle_options', 'max_attempts',
                'available_from', 'available_until'
            ]

            for field in allowed_fields:
                if field in data:
                    update_fields.append(f"{field} = ?")
                    params.append(data[field])

            if update_fields:
                query = f"UPDATE quizzes SET {', '.join(update_fields)} WHERE id = ?"
                params.append(quiz_id)
                cursor.execute(query, params)

            # Обновляем вопросы, если переданы
            if 'question_ids' in data:
                # Удаляем старые связи
                cursor.execute("DELETE FROM quiz_questions WHERE quiz_id = ?", (quiz_id,))

                # Добавляем новые
                for position, question_id in enumerate(data['question_ids']):
                    cursor.execute("""
                        INSERT INTO quiz_questions (quiz_id, question_id, position)
                        VALUES (?, ?, ?)
                    """, (quiz_id, question_id, position))

            return True

    def delete_quiz(self, quiz_id: int) -> bool:
        """Удалить викторину"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM quizzes WHERE id = ?", (quiz_id,))
            return cursor.rowcount > 0

    def add_question_to_quiz(self, quiz_id: int, question_id: int) -> bool:
        """
        Добавить вопрос в викторину

        Args:
            quiz_id: ID викторины
            question_id: ID вопроса

        Returns:
            True если вопрос добавлен успешно
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Проверяем, что викторина существует и имеет статус 'draft'
            cursor.execute("SELECT status FROM quizzes WHERE id = ?", (quiz_id,))
            row = cursor.fetchone()
            if not row:
                return False

            quiz_status = row['status']
            if quiz_status != 'draft':
                return False  # Нельзя добавлять вопросы в готовую викторину

            # Проверяем, что вопрос не добавлен уже
            cursor.execute("""
                SELECT id FROM quiz_questions
                WHERE quiz_id = ? AND question_id = ?
            """, (quiz_id, question_id))

            if cursor.fetchone():
                return False  # Вопрос уже добавлен

            # Получаем максимальную позицию
            cursor.execute("""
                SELECT MAX(position) as max_pos FROM quiz_questions WHERE quiz_id = ?
            """, (quiz_id,))

            result = cursor.fetchone()
            next_position = (result['max_pos'] or -1) + 1

            # Добавляем вопрос
            cursor.execute("""
                INSERT INTO quiz_questions (quiz_id, question_id, position)
                VALUES (?, ?, ?)
            """, (quiz_id, question_id, next_position))

            return cursor.rowcount > 0

    def remove_question_from_quiz(self, quiz_id: int, question_id: int) -> bool:
        """
        Удалить вопрос из викторины

        Args:
            quiz_id: ID викторины
            question_id: ID вопроса

        Returns:
            True если вопрос удален успешно
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Проверяем, что викторина имеет статус 'draft'
            cursor.execute("SELECT status FROM quizzes WHERE id = ?", (quiz_id,))
            row = cursor.fetchone()
            if not row or row['status'] != 'draft':
                return False

            # Удаляем вопрос
            cursor.execute("""
                DELETE FROM quiz_questions
                WHERE quiz_id = ? AND question_id = ?
            """, (quiz_id, question_id))

            return cursor.rowcount > 0

    def update_quiz_status(self, quiz_id: int, status: str) -> bool:
        """
        Изменить статус викторины

        Args:
            quiz_id: ID викторины
            status: Новый статус ('draft' или 'ready')

        Returns:
            True если статус обновлен успешно
        """
        if status not in ['draft', 'ready']:
            return False

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE quizzes SET status = ? WHERE id = ?
            """, (status, quiz_id))
            return cursor.rowcount > 0

    def _get_quiz_questions(self, quiz_id: int) -> List[Dict]:
        """Получить вопросы викторины"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    qq.position,
                    qq.points_override,
                    q.*
                FROM quiz_questions qq
                JOIN questions q ON qq.question_id = q.id
                WHERE qq.quiz_id = ?
                ORDER BY qq.position
            """, (quiz_id,))

            questions = []
            for row in cursor.fetchall():
                question = dict(row)
                question['options'] = self._get_options(question['id'])
                question['matching_pairs'] = self._get_matching_pairs(question['id'])
                question['tags'] = self._get_tags(question['id'])
                questions.append(question)

            return questions

    # ==================== ПРОХОЖДЕНИЕ ВИКТОРИНЫ ====================

    def start_quiz_attempt(
        self,
        quiz_id: int = None,
        unique_code: str = None,
        student_name: str = None,
        student_email: str = None,
        ip_address: str = None
    ) -> Optional[Dict]:
        """
        Начать новую попытку прохождения викторины

        Returns:
            Словарь с данными попытки, включая unique_session_id
        """
        # Получаем викторину
        quiz = self.get_quiz(quiz_id=quiz_id, unique_code=unique_code)

        if not quiz or not quiz.get('is_active'):
            return None

        # Проверяем доступность по времени
        now = datetime.now()
        if quiz.get('available_from'):
            available_from = datetime.fromisoformat(quiz['available_from'])
            if now < available_from:
                return None

        if quiz.get('available_until'):
            available_until = datetime.fromisoformat(quiz['available_until'])
            if now > available_until:
                return None

        # Проверяем количество попыток
        if quiz.get('max_attempts'):
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM quiz_attempts
                    WHERE quiz_id = ? AND student_name = ?
                """, (quiz['id'], student_name))

                count = cursor.fetchone()['count']
                if count >= quiz['max_attempts']:
                    return None

        # Создаем попытку
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Генерируем уникальный session_id
            session_id = secrets.token_urlsafe(32)

            cursor.execute("""
                INSERT INTO quiz_attempts (
                    quiz_id, student_name, student_email, unique_session_id,
                    total_questions, ip_address
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                quiz['id'], student_name, student_email, session_id,
                quiz['question_count'], ip_address
            ))

            attempt_id = cursor.lastrowid

            # Получаем созданную попытку
            cursor.execute("SELECT * FROM quiz_attempts WHERE id = ?", (attempt_id,))
            attempt = dict(cursor.fetchone())

            # Добавляем информацию о викторине
            attempt['quiz'] = quiz

            return attempt

    def submit_quiz_answer(
        self,
        session_id: str,
        question_id: int,
        answer: str,  # JSON string
        time_spent: int = None
    ) -> Dict:
        """
        Отправить ответ на вопрос

        Returns:
            Словарь с результатом проверки: {is_correct, points_earned, correct_answers}
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Получаем попытку
            cursor.execute("""
                SELECT * FROM quiz_attempts WHERE unique_session_id = ?
            """, (session_id,))

            attempt = cursor.fetchone()
            if not attempt:
                return {'error': 'Session not found'}

            attempt = dict(attempt)

            # Получаем вопрос
            question = self.get_question_by_id(question_id)
            if not question:
                return {'error': 'Question not found'}

            # Проверяем ответ
            is_correct, points_earned = self._check_answer(question, answer)

            # Сохраняем ответ
            cursor.execute("""
                INSERT INTO quiz_answers (
                    attempt_id, question_id, answer, is_correct, points_earned, time_spent
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (attempt['id'], question_id, answer, is_correct, points_earned, time_spent))

            return {
                'is_correct': is_correct,
                'points_earned': points_earned
            }

    def complete_quiz_attempt(self, session_id: str) -> Dict:
        """
        Завершить попытку и подсчитать результаты

        Returns:
            Словарь с результатами
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Получаем попытку
            cursor.execute("""
                SELECT * FROM quiz_attempts WHERE unique_session_id = ?
            """, (session_id,))

            attempt = cursor.fetchone()
            if not attempt:
                return {'error': 'Session not found'}

            attempt = dict(attempt)

            # Подсчитываем результаты
            cursor.execute("""
                SELECT
                    COUNT(*) as answered,
                    SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct,
                    SUM(points_earned) as points_earned,
                    SUM(time_spent) as time_spent
                FROM quiz_answers
                WHERE attempt_id = ?
            """, (attempt['id'],))

            results = dict(cursor.fetchone())

            # Подсчитываем максимальные баллы
            cursor.execute("""
                SELECT SUM(q.points) as points_total
                FROM quiz_questions qq
                JOIN questions q ON qq.question_id = q.id
                WHERE qq.quiz_id = ?
            """, (attempt['quiz_id'],))

            points_total = cursor.fetchone()['points_total'] or 0

            # Рассчитываем процент
            correct_answers = results['correct'] or 0
            total_questions = attempt['total_questions']
            score = (correct_answers / total_questions * 100) if total_questions > 0 else 0

            # Получаем порог прохождения
            cursor.execute("SELECT pass_threshold FROM quizzes WHERE id = ?", (attempt['quiz_id'],))
            pass_threshold = cursor.fetchone()['pass_threshold'] or 0
            is_passed = score >= pass_threshold

            # Обновляем попытку
            cursor.execute("""
                UPDATE quiz_attempts
                SET
                    completed_at = CURRENT_TIMESTAMP,
                    time_spent = ?,
                    correct_answers = ?,
                    score = ?,
                    points_earned = ?,
                    points_total = ?,
                    is_passed = ?
                WHERE id = ?
            """, (
                results['time_spent'], correct_answers, score,
                results['points_earned'], points_total, is_passed,
                attempt['id']
            ))

            return {
                'score': score,
                'correct_answers': correct_answers,
                'total_questions': total_questions,
                'points_earned': results['points_earned'],
                'points_total': points_total,
                'is_passed': is_passed,
                'time_spent': results['time_spent']
            }

    def _check_answer(self, question: Dict, user_answer: str) -> tuple:
        """
        Проверить ответ пользователя

        Returns:
            (is_correct, points_earned)
        """
        import json

        try:
            answer_data = json.loads(user_answer)
        except:
            answer_data = user_answer

        is_correct = False
        points = question.get('points', 1.0)

        if question['type'] in ['choice', 'multiple_choice']:
            # Для вариантов ответа
            correct_answers = [
                opt['text'] for opt in question['options']
                if opt['is_correct']
            ]

            if isinstance(answer_data, list):
                # Множественный выбор
                is_correct = set(answer_data) == set(correct_answers)
            else:
                # Одиночный выбор
                is_correct = answer_data in correct_answers

        elif question['type'] == 'text':
            # Для текстовых ответов
            correct_text = question.get('correct_text', '')
            is_correct = answer_data.lower().strip() == correct_text.lower().strip()

        points_earned = points if is_correct else 0
        return is_correct, points_earned

    # ==================== РЕЗУЛЬТАТЫ И СТАТИСТИКА ====================

    def get_quiz_attempts(
        self,
        quiz_id: int,
        completed_only: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """Получить попытки прохождения викторины"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM quiz_attempts WHERE quiz_id = ?"
            params = [quiz_id]

            if completed_only:
                query += " AND completed_at IS NOT NULL"

            query += " ORDER BY started_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_attempt_details(self, attempt_id: int = None, session_id: str = None) -> Optional[Dict]:
        """Получить детальную информацию о попытке"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            if attempt_id:
                cursor.execute("SELECT * FROM quiz_attempts WHERE id = ?", (attempt_id,))
            elif session_id:
                cursor.execute("SELECT * FROM quiz_attempts WHERE unique_session_id = ?", (session_id,))
            else:
                return None

            row = cursor.fetchone()
            if not row:
                return None

            attempt = dict(row)

            # Получаем ответы
            cursor.execute("""
                SELECT
                    qa.*,
                    q.text as question_text,
                    q.type as question_type
                FROM quiz_answers qa
                JOIN questions q ON qa.question_id = q.id
                WHERE qa.attempt_id = ?
                ORDER BY qa.answered_at
            """, (attempt['id'],))

            attempt['answers'] = [dict(row) for row in cursor.fetchall()]

            return attempt
