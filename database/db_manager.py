"""
Менеджер базы данных для работы с вопросами олимпиад
"""
import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from contextlib import contextmanager
from .quiz_manager import QuizManager


class DatabaseManager(QuizManager):
    """Менеджер для работы с SQLite базой данных"""

    def __init__(self, db_path: str = "olympiad_questions.db"):
        self.db_path = Path(db_path)
        self.init_database()

    @contextmanager
    def get_connection(self):
        """Контекстный менеджер для работы с подключением"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Доступ к колонкам по имени
        conn.execute("PRAGMA foreign_keys = ON")  # Включаем внешние ключи
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def init_database(self):
        """Инициализация базы данных из schema.sql"""
        schema_path = Path(__file__).parent / "schema.sql"

        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")

        with self.get_connection() as conn:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = f.read()
                conn.executescript(schema)

        print(f"✅ База данных инициализирована: {self.db_path}")

    # ==================== ДОБАВЛЕНИЕ ДАННЫХ ====================

    def add_question(
        self,
        text: str,
        question_type: str,
        options: List[Dict] = None,
        matching_pairs: List[Tuple[str, str]] = None,
        tags: Dict[str, List[str]] = None,
        difficulty: int = 1,
        points: float = 1.0,
        explanation: str = None,
        source_pdf: str = None,
        page_number: int = None
    ) -> int:
        """
        Добавить вопрос в базу данных

        Args:
            text: Текст вопроса
            question_type: Тип вопроса ('choice', 'multiple_choice', 'matching', 'text')
            options: Список вариантов ответов [{"text": "...", "is_correct": True/False}]
            matching_pairs: Список пар для соответствия [("левая часть", "правая часть")]
            tags: Словарь тегов {"subject": ["Обществознание"], "year": ["2024"], ...}
            difficulty: Сложность 1-5
            points: Баллы за вопрос
            explanation: Объяснение правильного ответа
            source_pdf: Путь к исходному PDF
            page_number: Номер страницы в PDF

        Returns:
            ID добавленного вопроса

        Raises:
            ValueError: Если вопрос типа choice/multiple_choice не имеет вариантов ответа
                       или вопрос типа matching не имеет пар соответствия
        """
        # Валидация: проверяем наличие вариантов ответа
        if question_type in ['choice', 'multiple_choice']:
            if not options or len(options) == 0:
                raise ValueError(
                    f"Вопрос типа '{question_type}' должен иметь хотя бы один вариант ответа"
                )

        # Валидация: проверяем наличие пар соответствия
        if question_type == 'matching':
            if not matching_pairs or len(matching_pairs) == 0:
                raise ValueError(
                    "Вопрос типа 'matching' должен иметь хотя бы одну пару соответствия"
                )

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Добавляем вопрос
            cursor.execute("""
                INSERT INTO questions (text, type, difficulty, points, explanation, source_pdf, page_number)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (text, question_type, difficulty, points, explanation, source_pdf, page_number))

            question_id = cursor.lastrowid

            # Добавляем варианты ответов
            if options and question_type in ['choice', 'multiple_choice']:
                for i, option in enumerate(options):
                    cursor.execute("""
                        INSERT INTO options (question_id, text, is_correct, position)
                        VALUES (?, ?, ?, ?)
                    """, (question_id, option['text'], option.get('is_correct', False), i))

            # Добавляем пары для соответствия
            if matching_pairs and question_type == 'matching':
                for i, (left, right) in enumerate(matching_pairs):
                    cursor.execute("""
                        INSERT INTO matching_pairs (question_id, left_text, right_text, position)
                        VALUES (?, ?, ?, ?)
                    """, (question_id, left, right, i))

            # Добавляем теги
            if tags:
                for category, values in tags.items():
                    for value in values:
                        cursor.execute("""
                            INSERT INTO tags (question_id, category, value)
                            VALUES (?, ?, ?)
                        """, (question_id, category, value))

            return question_id

    # ==================== ПОИСК И ФИЛЬТРАЦИЯ ====================

    def get_questions(
        self,
        subject: str = None,
        university: str = None,
        year: str = None,
        question_type: str = None,
        difficulty: int = None,
        topic: str = None,
        verified: str = None,
        source_pdf: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """
        Получить вопросы с фильтрацией

        Returns:
            Список вопросов с вариантами ответов
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Если используется только source_pdf, упрощаем запрос
            if source_pdf and not any([subject, university, year, topic]):
                query = "SELECT * FROM questions WHERE source_pdf = ?"
                params = [source_pdf]

                if question_type:
                    query += " AND type = ?"
                    params.append(question_type)

                if difficulty:
                    query += " AND difficulty = ?"
                    params.append(difficulty)

                if verified is not None:
                    if verified.lower() == 'true':
                        query += " AND verified = 1"
                    elif verified.lower() == 'false':
                        query += " AND (verified = 0 OR verified IS NULL)"

                query += " ORDER BY id LIMIT ? OFFSET ?"
                params.extend([limit, offset])

                cursor.execute(query, params)
                questions = [dict(row) for row in cursor.fetchall()]
            else:
                # Базовый запрос с JOIN для tag-based фильтрации
                query = """
                    SELECT DISTINCT q.* FROM questions q
                    LEFT JOIN tags t ON q.id = t.question_id
                    WHERE 1=1
                """
                params = []

                # Добавляем фильтры
                if subject:
                    query += " AND t.category = 'subject' AND t.value = ?"
                    params.append(subject)

                if university:
                    query += " AND EXISTS (SELECT 1 FROM tags t2 WHERE t2.question_id = q.id AND t2.category = 'university' AND t2.value = ?)"
                    params.append(university)

                if year:
                    query += " AND EXISTS (SELECT 1 FROM tags t3 WHERE t3.question_id = q.id AND t3.category = 'year' AND t3.value = ?)"
                    params.append(year)

                if question_type:
                    query += " AND q.type = ?"
                    params.append(question_type)

                if difficulty:
                    query += " AND q.difficulty = ?"
                    params.append(difficulty)

                if topic:
                    query += " AND EXISTS (SELECT 1 FROM tags t4 WHERE t4.question_id = q.id AND t4.category = 'topic' AND t4.value LIKE ?)"
                    params.append(f"%{topic}%")

                if verified is not None:
                    if verified.lower() == 'true':
                        query += " AND q.verified = 1"
                    elif verified.lower() == 'false':
                        query += " AND (q.verified = 0 OR q.verified IS NULL)"

                if source_pdf:
                    query += " AND q.source_pdf = ?"
                    params.append(source_pdf)

                query += " ORDER BY q.id LIMIT ? OFFSET ?"
                params.extend([limit, offset])

                cursor.execute(query, params)
                questions = [dict(row) for row in cursor.fetchall()]

            # Дополняем каждый вопрос вариантами ответов и тегами
            for question in questions:
                question['options'] = self._get_options(question['id'])
                question['matching_pairs'] = self._get_matching_pairs(question['id'])
                question['tags'] = self._get_tags(question['id'])

            return questions

    def get_question_by_id(self, question_id: int) -> Optional[Dict]:
        """Получить конкретный вопрос по ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM questions WHERE id = ?", (question_id,))
            row = cursor.fetchone()

            if not row:
                return None

            question = dict(row)
            question['options'] = self._get_options(question_id)
            question['matching_pairs'] = self._get_matching_pairs(question_id)
            question['tags'] = self._get_tags(question_id)

            return question

    def _get_options(self, question_id: int) -> List[Dict]:
        """Получить варианты ответов для вопроса"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, text, is_correct, position
                FROM options
                WHERE question_id = ?
                ORDER BY position
            """, (question_id,))
            return [dict(row) for row in cursor.fetchall()]

    def _get_matching_pairs(self, question_id: int) -> List[Dict]:
        """Получить пары для соответствия"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, left_text, right_text, position
                FROM matching_pairs
                WHERE question_id = ?
                ORDER BY position
            """, (question_id,))
            return [dict(row) for row in cursor.fetchall()]

    def _get_tags(self, question_id: int) -> Dict[str, List[str]]:
        """Получить теги вопроса"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT category, value
                FROM tags
                WHERE question_id = ?
            """, (question_id,))

            tags = {}
            for row in cursor.fetchall():
                category = row['category']
                value = row['value']
                if category not in tags:
                    tags[category] = []
                tags[category].append(value)

            return tags

    # ==================== УПРАВЛЕНИЕ PDF ФАЙЛАМИ ====================

    def get_pdfs(
        self,
        university: str = None,
        olympiad: str = None,
        year: str = None,
        subject: str = None,
        search: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """
        Получить список PDF файлов с фильтрацией

        Args:
            university: Фильтр по университету
            olympiad: Фильтр по олимпиаде
            year: Фильтр по году
            subject: Фильтр по предмету
            search: Поиск по display_name или file_path
            limit: Максимальное количество результатов
            offset: Смещение для пагинации

        Returns:
            Список PDF файлов с метаданными
        """
        query = """
            SELECT
                id, file_path, display_name, university, olympiad,
                year, subject, is_manual, question_count,
                verification_status, manual_verification_override,
                created_at, updated_at
            FROM pdf_files
            WHERE 1=1
        """
        params = []

        if university:
            query += " AND university = ?"
            params.append(university)

        if olympiad:
            query += " AND olympiad = ?"
            params.append(olympiad)

        if year:
            query += " AND year = ?"
            params.append(year)

        if subject:
            query += " AND subject = ?"
            params.append(subject)

        if search:
            query += " AND (display_name LIKE ? OR file_path LIKE ?)"
            search_pattern = f"%{search}%"
            params.extend([search_pattern, search_pattern])

        query += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_pdf_by_id(self, pdf_id: int) -> Dict:
        """
        Получить PDF файл по ID

        Args:
            pdf_id: ID PDF файла

        Returns:
            Словарь с метаданными PDF или None
        """
        query = """
            SELECT
                id, file_path, display_name, university, olympiad,
                year, subject, is_manual, question_count,
                verification_status, manual_verification_override,
                created_at, updated_at
            FROM pdf_files
            WHERE id = ?
        """

        with self.get_connection() as conn:
            cursor = conn.execute(query, [pdf_id])
            columns = [description[0] for description in cursor.description]
            row = cursor.fetchone()
            if row:
                return dict(zip(columns, row))
            return None

    def update_pdf_metadata(
        self,
        pdf_id: int,
        display_name: str = None,
        university: str = None,
        olympiad: str = None,
        year: str = None,
        subject: str = None,
        cascade_to_questions: bool = True
    ) -> bool:
        """
        Обновить метаданные PDF файла

        Args:
            pdf_id: ID PDF файла
            display_name: Новое отображаемое имя
            university: Университет
            olympiad: Олимпиада
            year: Год
            subject: Предмет
            cascade_to_questions: Если True, обновить теги всех вопросов из этого PDF

        Returns:
            True если успешно, False иначе
        """
        # Получить текущий PDF
        pdf = self.get_pdf_by_id(pdf_id)
        if not pdf:
            return False

        # Подготовить обновления
        update_parts = []
        params = []

        if display_name is not None:
            update_parts.append("display_name = ?")
            params.append(display_name)

        if university is not None:
            update_parts.append("university = ?")
            params.append(university)

        if olympiad is not None:
            update_parts.append("olympiad = ?")
            params.append(olympiad)

        if year is not None:
            update_parts.append("year = ?")
            params.append(year)

        if subject is not None:
            update_parts.append("subject = ?")
            params.append(subject)

        if not update_parts:
            return True  # Нечего обновлять

        params.append(pdf_id)

        with self.get_connection() as conn:
            # Обновить PDF
            query = f"UPDATE pdf_files SET {', '.join(update_parts)} WHERE id = ?"
            conn.execute(query, params)

            # Каскадное обновление вопросов
            if cascade_to_questions:
                file_path = pdf['file_path']

                # Получить все вопросы из этого PDF
                cursor = conn.execute(
                    "SELECT id FROM questions WHERE source_pdf = ?",
                    [file_path]
                )
                question_ids = [row[0] for row in cursor.fetchall()]

                # Для каждого вопроса обновить теги
                for question_id in question_ids:
                    # Удалить старые теги соответствующих категорий
                    categories_to_update = []

                    if university is not None:
                        categories_to_update.append('university')
                    if olympiad is not None:
                        categories_to_update.append('olympiad')
                    if year is not None:
                        categories_to_update.append('year')
                    if subject is not None:
                        categories_to_update.append('subject')

                    if categories_to_update:
                        placeholders = ', '.join(['?'] * len(categories_to_update))
                        delete_query = f"""
                            DELETE FROM tags
                            WHERE question_id = ? AND category IN ({placeholders})
                        """
                        conn.execute(delete_query, [question_id] + categories_to_update)

                        # Добавить новые теги
                        for category in categories_to_update:
                            value = None
                            if category == 'university' and university is not None:
                                value = university
                            elif category == 'olympiad' and olympiad is not None:
                                value = olympiad
                            elif category == 'year' and year is not None:
                                value = year
                            elif category == 'subject' and subject is not None:
                                value = subject

                            if value:
                                conn.execute(
                                    "INSERT INTO tags (question_id, category, value) VALUES (?, ?, ?)",
                                    [question_id, category, value]
                                )

            conn.commit()
            return True

    def create_pdf_entry(
        self,
        display_name: str,
        university: str = None,
        olympiad: str = None,
        year: str = None,
        subject: str = None
    ) -> int:
        """
        Создать запись PDF для ручных вопросов (без реального файла)

        Args:
            display_name: Отображаемое имя
            university: Университет
            olympiad: Олимпиада
            year: Год
            subject: Предмет

        Returns:
            ID созданного PDF или None при ошибке
        """
        from datetime import datetime

        # Сгенерировать уникальный file_path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in display_name)
        file_path = f"manual/{timestamp}_{safe_name}"

        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO pdf_files
                (file_path, display_name, university, olympiad, year, subject, is_manual)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            """, [file_path, display_name, university, olympiad, year, subject])

            conn.commit()
            return cursor.lastrowid

    # ==================== ОБНОВЛЕНИЕ ДАННЫХ ====================

    def update_question(self, question_id: int, data: Dict) -> bool:
        """
        Обновить вопрос

        Args:
            question_id: ID вопроса
            data: Словарь с данными для обновления
                {
                    "text": str,
                    "type": str,
                    "difficulty": int,
                    "points": float,
                    "explanation": str,
                    "verified": bool,
                    "options": List[Dict],
                    "tags": Dict[str, List[str]]
                }

        Returns:
            True если обновление успешно, False если вопрос не найден

        Raises:
            ValueError: Если обновление нарушает требования валидации
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Проверяем существование вопроса и получаем текущий тип
            cursor.execute("SELECT id, type FROM questions WHERE id = ?", (question_id,))
            row = cursor.fetchone()
            if not row:
                return False

            current_type = row[1]
            new_type = data.get('type', current_type)

            # Валидация при изменении типа или опций
            if 'type' in data or 'options' in data:
                # Если новый тип - choice/multiple_choice, проверяем наличие вариантов
                if new_type in ['choice', 'multiple_choice']:
                    if 'options' in data:
                        # Если обновляем варианты, проверяем что они не пустые
                        if not data['options'] or len(data['options']) == 0:
                            raise ValueError(
                                f"Вопрос типа '{new_type}' должен иметь хотя бы один вариант ответа"
                            )
                    elif new_type != current_type:
                        # Если меняем тип, проверяем что в БД уже есть варианты
                        cursor.execute(
                            "SELECT COUNT(*) as count FROM options WHERE question_id = ?",
                            (question_id,)
                        )
                        if cursor.fetchone()[0] == 0:
                            raise ValueError(
                                f"Нельзя изменить тип вопроса на '{new_type}' без вариантов ответа"
                            )

            # Обновляем поля вопроса
            update_fields = []
            params = []

            if 'text' in data:
                update_fields.append("text = ?")
                params.append(data['text'])

            if 'type' in data:
                update_fields.append("type = ?")
                params.append(data['type'])

            if 'difficulty' in data:
                update_fields.append("difficulty = ?")
                params.append(data['difficulty'])

            if 'points' in data:
                update_fields.append("points = ?")
                params.append(data['points'])

            if 'explanation' in data:
                update_fields.append("explanation = ?")
                params.append(data['explanation'])

            if 'verified' in data:
                update_fields.append("verified = ?")
                params.append(1 if data['verified'] else 0)
                if data['verified']:
                    update_fields.append("verified_at = ?")
                    params.append(datetime.now().isoformat())

            if update_fields:
                query = f"UPDATE questions SET {', '.join(update_fields)} WHERE id = ?"
                params.append(question_id)
                cursor.execute(query, params)

            # Обновляем варианты ответов
            if 'options' in data:
                # Удаляем старые опции
                cursor.execute("DELETE FROM options WHERE question_id = ?", (question_id,))

                # Добавляем новые
                for i, option in enumerate(data['options']):
                    cursor.execute("""
                        INSERT INTO options (question_id, text, is_correct, position)
                        VALUES (?, ?, ?, ?)
                    """, (question_id, option['text'], option.get('is_correct', False), i))

            # Обновляем пары соответствия
            if 'matching_pairs' in data:
                # Удаляем старые пары
                cursor.execute("DELETE FROM matching_pairs WHERE question_id = ?", (question_id,))

                # Добавляем новые
                for i, pair in enumerate(data['matching_pairs']):
                    cursor.execute("""
                        INSERT INTO matching_pairs (question_id, left_text, right_text, position)
                        VALUES (?, ?, ?, ?)
                    """, (question_id, pair['left_text'], pair['right_text'], i))

            # Обновляем теги
            if 'tags' in data:
                # Удаляем старые теги
                cursor.execute("DELETE FROM tags WHERE question_id = ?", (question_id,))

                # Добавляем новые
                for category, values in data['tags'].items():
                    for value in values:
                        cursor.execute("""
                            INSERT INTO tags (question_id, category, value)
                            VALUES (?, ?, ?)
                        """, (question_id, category, value))

            return True

    # ==================== СТАТИСТИКА ====================

    def get_stats(self) -> Dict:
        """Получить общую статистику"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            stats = {}

            # Общее количество вопросов
            cursor.execute("SELECT COUNT(*) as count FROM questions")
            stats['total_questions'] = cursor.fetchone()['count']

            # По типам
            cursor.execute("""
                SELECT type, COUNT(*) as count
                FROM questions
                GROUP BY type
            """)
            stats['by_type'] = {row['type']: row['count'] for row in cursor.fetchall()}

            # По предметам
            cursor.execute("""
                SELECT t.value as subject, COUNT(DISTINCT q.id) as count
                FROM questions q
                JOIN tags t ON q.id = t.question_id
                WHERE t.category = 'subject'
                GROUP BY t.value
                ORDER BY count DESC
            """)
            stats['by_subject'] = {row['subject']: row['count'] for row in cursor.fetchall()}

            # По университетам
            cursor.execute("""
                SELECT t.value as university, COUNT(DISTINCT q.id) as count
                FROM questions q
                JOIN tags t ON q.id = t.question_id
                WHERE t.category = 'university'
                GROUP BY t.value
                ORDER BY count DESC
            """)
            stats['by_university'] = {row['university']: row['count'] for row in cursor.fetchall()}

            # По годам
            cursor.execute("""
                SELECT t.value as year, COUNT(DISTINCT q.id) as count
                FROM questions q
                JOIN tags t ON q.id = t.question_id
                WHERE t.category = 'year'
                GROUP BY t.value
                ORDER BY year DESC
            """)
            stats['by_year'] = {row['year']: row['count'] for row in cursor.fetchall()}

            return stats

    def get_filter_values(self) -> Dict[str, List[str]]:
        """Получить все доступные значения для фильтров"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            filters = {}

            # Предметы
            cursor.execute("""
                SELECT DISTINCT value FROM tags WHERE category = 'subject' ORDER BY value
            """)
            filters['subjects'] = [row['value'] for row in cursor.fetchall()]

            # Университеты
            cursor.execute("""
                SELECT DISTINCT value FROM tags WHERE category = 'university' ORDER BY value
            """)
            filters['universities'] = [row['value'] for row in cursor.fetchall()]

            # Годы
            cursor.execute("""
                SELECT DISTINCT value FROM tags WHERE category = 'year' ORDER BY value DESC
            """)
            filters['years'] = [row['value'] for row in cursor.fetchall()]

            # Типы вопросов
            cursor.execute("""
                SELECT DISTINCT type FROM questions ORDER BY type
            """)
            filters['question_types'] = [row['type'] for row in cursor.fetchall()]

            return filters


if __name__ == "__main__":
    # Тестирование
    db = DatabaseManager("test_olympiad.db")

    # Добавляем тестовый вопрос
    question_id = db.add_question(
        text="Какой из перечисленных философов является представителем немецкой классической философии?",
        question_type="choice",
        options=[
            {"text": "Платон", "is_correct": False},
            {"text": "Иммануил Кант", "is_correct": True},
            {"text": "Джон Локк", "is_correct": False},
            {"text": "Фома Аквинский", "is_correct": False}
        ],
        tags={
            "subject": ["Философия"],
            "university": ["МГУ"],
            "year": ["2024"],
            "stage": ["Отборочный тур"]
        },
        difficulty=2,
        points=2.0
    )

    print(f"✅ Добавлен вопрос ID: {question_id}")

    # Получаем статистику
    stats = db.get_stats()
    print(f"\n📊 Статистика:")
    print(f"  Всего вопросов: {stats['total_questions']}")
    print(f"  По предметам: {stats['by_subject']}")

    # Получаем вопросы
    questions = db.get_questions(subject="Философия")
    print(f"\n📝 Найдено вопросов по философии: {len(questions)}")
    if questions:
        print(f"  Первый вопрос: {questions[0]['text'][:100]}...")
