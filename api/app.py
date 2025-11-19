"""
Flask API для работы с олимпиадными вопросами
"""
import sys
from pathlib import Path

# Добавляем путь к корню проекта
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from database.db_manager import DatabaseManager
from dotenv import load_dotenv
import json
import os
import subprocess
import sqlite3
from datetime import datetime

# Загружаем переменные окружения из .env файла
load_dotenv()

app = Flask(__name__)
CORS(app)  # Разрешаем CORS для работы с фронтендом

# Инициализируем БД с абсолютным путем к корню проекта
DB_PATH = Path(__file__).parent.parent / "olympiad_questions.db"
db = DatabaseManager(str(DB_PATH))


@app.route('/api/health', methods=['GET'])
def health():
    """Проверка работоспособности API"""
    return jsonify({
        "status": "ok",
        "message": "API работает"
    })


@app.route('/api/questions', methods=['GET'])
def get_questions():
    """
    Получить список вопросов с фильтрацией

    Query params:
        - subject: предмет
        - university: университет
        - year: год
        - question_type: тип вопроса
        - difficulty: сложность
        - topic: тема
        - verified: только проверенные (true/false)
        - source_pdf: путь к исходному PDF файлу
        - search_text: поиск по тексту вопроса (поддержка масок: *возрожд*)
        - tags: список тегов через запятую (например: ницше,возрождение)
        - limit: количество вопросов (по умолчанию 50)
        - offset: смещение для пагинации
    """
    try:
        # Получаем параметры фильтрации
        subject = request.args.get('subject')
        university = request.args.get('university')
        year = request.args.get('year')
        question_type = request.args.get('question_type')
        difficulty = request.args.get('difficulty', type=int)
        topic = request.args.get('topic')
        verified = request.args.get('verified')
        source_pdf = request.args.get('source_pdf')
        search_text = request.args.get('search_text')
        tags_param = request.args.get('tags')
        limit = request.args.get('limit', default=50, type=int)
        offset = request.args.get('offset', default=0, type=int)

        # Парсим теги если они есть
        tags = None
        if tags_param:
            tags = [tag.strip() for tag in tags_param.split(',') if tag.strip()]

        # Получаем вопросы
        questions = db.get_questions(
            subject=subject,
            university=university,
            year=year,
            question_type=question_type,
            difficulty=difficulty,
            topic=topic,
            verified=verified,
            source_pdf=source_pdf,
            search_text=search_text,
            tags=tags,
            limit=limit,
            offset=offset
        )

        return jsonify({
            "success": True,
            "count": len(questions),
            "questions": questions,
            "filters": {
                "subject": subject,
                "university": university,
                "year": year,
                "question_type": question_type,
                "difficulty": difficulty,
                "topic": topic,
                "search_text": search_text,
                "tags": tags
            }
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/questions/<int:question_id>', methods=['GET'])
def get_question(question_id):
    """Получить конкретный вопрос по ID"""
    try:
        question = db.get_question_by_id(question_id)

        if not question:
            return jsonify({
                "success": False,
                "error": "Вопрос не найден"
            }), 404

        return jsonify({
            "success": True,
            "question": question
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/filters', methods=['GET'])
def get_filters():
    """
    Получить доступные значения для фильтров
    (предметы, университеты, годы, типы вопросов)
    """
    try:
        filters = db.get_filter_values()

        return jsonify({
            "success": True,
            "filters": filters
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Получить общую статистику по вопросам"""
    try:
        stats = db.get_stats()

        return jsonify({
            "success": True,
            "stats": stats
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==================== УПРАВЛЕНИЕ ТЕГАМИ ====================

@app.route('/api/tags', methods=['GET'])
def get_all_tags():
    """
    Получить все уникальные теги

    Query params:
        - category: фильтр по категории (опционально)
    """
    try:
        category = request.args.get('category')
        tags = db.get_all_tags(category=category)

        return jsonify({
            "success": True,
            "tags": tags
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/questions/<int:question_id>/tags', methods=['POST'])
def add_question_tag(question_id):
    """
    Добавить тег к вопросу

    Body:
        - category: категория тега ('custom', 'topic', и т.д.)
        - value: значение тега
    """
    try:
        data = request.get_json()

        if not data or 'category' not in data or 'value' not in data:
            return jsonify({
                "success": False,
                "error": "Необходимо указать category и value"
            }), 400

        tag_id = db.add_tag(
            question_id=question_id,
            category=data['category'],
            value=data['value']
        )

        return jsonify({
            "success": True,
            "tag_id": tag_id
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/questions/<int:question_id>/tags', methods=['DELETE'])
def remove_question_tag(question_id):
    """
    Удалить тег из вопроса

    Body:
        - category: категория тега
        - value: значение тега
    """
    try:
        data = request.get_json()

        if not data or 'category' not in data or 'value' not in data:
            return jsonify({
                "success": False,
                "error": "Необходимо указать category и value"
            }), 400

        removed = db.remove_tag(
            question_id=question_id,
            category=data['category'],
            value=data['value']
        )

        return jsonify({
            "success": True,
            "removed": removed
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/questions/<int:question_id>/tags/<category>', methods=['PUT'])
def update_question_tags(question_id, category):
    """
    Обновить теги вопроса определенной категории

    Body:
        - tags: список тегов ['tag1', 'tag2', ...]
    """
    try:
        data = request.get_json()

        if not data or 'tags' not in data:
            return jsonify({
                "success": False,
                "error": "Необходимо указать tags"
            }), 400

        if not isinstance(data['tags'], list):
            return jsonify({
                "success": False,
                "error": "tags должен быть массивом"
            }), 400

        db.update_question_tags(
            question_id=question_id,
            category=category,
            tags=data['tags']
        )

        return jsonify({
            "success": True
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/random', methods=['GET'])
def get_random_questions():
    """
    Получить случайные вопросы для тестирования

    Query params:
        - count: количество вопросов (по умолчанию 10)
        - subject: предмет (опционально)
        - difficulty: сложность (опционально)
    """
    try:
        count = request.args.get('count', default=10, type=int)
        subject = request.args.get('subject')
        difficulty = request.args.get('difficulty', type=int)

        # Получаем вопросы с фильтрацией + случайный порядок
        questions = db.get_questions(
            subject=subject,
            difficulty=difficulty,
            limit=count
        )

        # Перемешиваем
        import random
        random.shuffle(questions)

        return jsonify({
            "success": True,
            "count": len(questions),
            "questions": questions
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/questions/<int:question_id>', methods=['PUT'])
def update_question(question_id):
    """
    Обновить вопрос

    Body:
        {
            "text": "Новый текст вопроса",
            "type": "choice",
            "difficulty": 3,
            "points": 2.0,
            "options": [{"text": "...", "is_correct": true}, ...],
            "tags": {"subject": ["Философия"], "university": ["МГУ"], ...},
            "verified": true
        }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "Нет данных для обновления"
            }), 400

        # Обновляем вопрос в БД
        result = db.update_question(question_id, data)

        if result:
            return jsonify({
                "success": True,
                "message": "Вопрос обновлён",
                "question_id": question_id
            })
        else:
            return jsonify({
                "success": False,
                "error": "Вопрос не найден"
            }), 404

    except Exception as e:
        error_msg = str(e)
        # Проверяем, является ли это ошибкой валидации из триггера
        if "Нельзя удалить последний вариант" in error_msg or "варианта ответа" in error_msg:
            return jsonify({
                "success": False,
                "error": error_msg
            }), 400
        else:
            return jsonify({
                "success": False,
                "error": error_msg
            }), 500


@app.route('/api/questions/<int:question_id>', methods=['DELETE'])
def delete_question(question_id):
    """
    Удалить вопрос

    Returns:
        {"success": true, "message": "..."}
    """
    try:
        conn = sqlite3.connect('olympiad_questions.db')
        cursor = conn.cursor()

        # Проверяем существование вопроса
        cursor.execute("SELECT id FROM questions WHERE id = ?", (question_id,))
        question = cursor.fetchone()

        if not question:
            conn.close()
            return jsonify({
                "success": False,
                "error": "Вопрос не найден"
            }), 404

        # Удаляем связанные данные
        # ВАЖНО: Удаляем в таком порядке, чтобы избежать срабатывания триггеров
        # 1. Сначала удаляем сам вопрос (это отключит некоторые триггеры)
        cursor.execute("DELETE FROM questions WHERE id = ?", (question_id,))

        # 2. Затем очищаем orphaned записи, если они остались
        cursor.execute("DELETE FROM tags WHERE question_id = ?", (question_id,))
        cursor.execute("DELETE FROM options WHERE question_id = ?", (question_id,))
        cursor.execute("DELETE FROM matching_pairs WHERE question_id = ?", (question_id,))

        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Вопрос успешно удалён"
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/questions', methods=['POST'])
def create_question():
    """
    Создать новый вопрос

    Body:
        {
            "text": "Текст вопроса",
            "type": "choice",
            "difficulty": 3,
            "points": 2.0,
            "options": [{"text": "...", "is_correct": true}, ...],
            "tags": {"subject": ["Философия"], ...},
            "source_pdf": "path/to/file.pdf" (optional),
            "verified": false
        }

    Returns:
        {"success": true, "question_id": 123}
    """
    try:
        data = request.get_json()

        if not data or not data.get('text'):
            return jsonify({
                "success": False,
                "error": "Текст вопроса обязателен"
            }), 400

        # Создаем вопрос через DatabaseManager
        question_id = db.add_question(
            text=data.get('text'),
            question_type=data.get('type'),
            options=data.get('options'),
            matching_pairs=data.get('matching_pairs'),
            tags=data.get('tags'),
            difficulty=data.get('difficulty', 1),
            points=data.get('points', 1.0),
            explanation=data.get('explanation'),
            source_pdf=data.get('source_pdf'),
            page_number=data.get('page_number'),
            correct_text=data.get('correct_text')
        )

        if question_id:
            # Получаем полный объект вопроса
            question = db.get_question_by_id(question_id)
            return jsonify({
                "success": True,
                "message": "Вопрос создан",
                "question_id": question_id,
                "question": question
            }), 201
        else:
            return jsonify({
                "success": False,
                "error": "Не удалось создать вопрос"
            }), 500

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/check_answer', methods=['POST'])
def check_answer():
    """
    Проверить ответ на вопрос

    Body:
        {
            "question_id": 1,
            "answer": ["Вариант 1", "Вариант 2"]  # или строка для текстового ответа
        }
    """
    try:
        data = request.get_json()
        question_id = data.get('question_id')
        user_answer = data.get('answer')

        if not question_id or user_answer is None:
            return jsonify({
                "success": False,
                "error": "Необходимо указать question_id и answer"
            }), 400

        # Получаем вопрос
        question = db.get_question_by_id(question_id)

        if not question:
            return jsonify({
                "success": False,
                "error": "Вопрос не найден"
            }), 404

        # Проверяем ответ
        is_correct = False
        correct_answers = []

        if question['type'] in ['choice', 'multiple_choice']:
            # Для вариантов ответа
            correct_answers = [
                opt['text'] for opt in question['options']
                if opt['is_correct']
            ]

            if isinstance(user_answer, list):
                # Множественный выбор
                is_correct = set(user_answer) == set(correct_answers)
            else:
                # Одиночный выбор
                is_correct = user_answer in correct_answers

        elif question['type'] == 'text':
            # Для текстовых ответов - простое сравнение
            # TODO: добавить нормализацию и нечеткое сравнение
            correct_answers = [question.get('correct_text', '')]
            is_correct = user_answer.lower().strip() == correct_answers[0].lower().strip()

        return jsonify({
            "success": True,
            "is_correct": is_correct,
            "correct_answers": correct_answers,
            "user_answer": user_answer
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==================== ВИКТОРИНЫ ====================

@app.route('/api/source-pdfs', methods=['GET'])
def get_source_pdfs():
    """
    Получить список всех PDF файлов из которых были импортированы вопросы
    """
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    source_pdf,
                    COUNT(*) as question_count,
                    MIN(page_number) as first_page,
                    MAX(page_number) as last_page
                FROM questions
                WHERE source_pdf IS NOT NULL
                GROUP BY source_pdf
                ORDER BY source_pdf
            """)

            pdfs = []
            for row in cursor.fetchall():
                pdf_path = row['source_pdf']
                pdfs.append({
                    'path': pdf_path,
                    'filename': Path(pdf_path).name if pdf_path else None,
                    'question_count': row['question_count'],
                    'page_range': f"{row['first_page']}-{row['last_page']}" if row['first_page'] else None
                })

            return jsonify({
                "success": True,
                "pdfs": pdfs,
                "count": len(pdfs)
            })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/questions/by-pdf', methods=['GET'])
def get_questions_by_pdf():
    """
    Получить вопросы из конкретного PDF файла

    Query params:
        - source_pdf: путь к PDF файлу
    """
    try:
        source_pdf = request.args.get('source_pdf')

        if not source_pdf:
            return jsonify({
                "success": False,
                "error": "Параметр source_pdf обязателен"
            }), 400

        # FIX: Properly handle URL encoding with Cyrillic characters
        # Flask decodes URL escapes but may use wrong encoding
        # Re-encode as latin-1 and decode as utf-8 to fix Cyrillic
        try:
            source_pdf = source_pdf.encode('latin-1').decode('utf-8')
        except (UnicodeDecodeError, UnicodeEncodeError):
            # If conversion fails, use as-is (already correctly encoded)
            pass

        # Прямой запрос к БД без использования get_questions
        import sqlite3
        conn = sqlite3.connect('olympiad_questions.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM questions WHERE source_pdf = ? ORDER BY id LIMIT 10000", [source_pdf])
        rows = cursor.fetchall()

        questions = []
        for row in rows:
            q = dict(row)
            # Получить опции
            cursor.execute("SELECT id, text, is_correct FROM options WHERE question_id = ?", [q['id']])
            q['options'] = [dict(opt) for opt in cursor.fetchall()]
            # Получить теги
            cursor.execute("SELECT category, value FROM tags WHERE question_id = ?", [q['id']])
            tags = {}
            for tag in cursor.fetchall():
                cat, val = tag['category'], tag['value']
                if cat not in tags:
                    tags[cat] = []
                tags[cat].append(val)
            q['tags'] = tags
            questions.append(q)

        conn.close()

        return jsonify({
            "success": True,
            "questions": questions,
            "count": len(questions),
            "source_pdf": source_pdf
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/quizzes', methods=['GET', 'POST'])
def quizzes():
    """
    GET: Получить список викторин
    POST: Создать новую викторину
    """
    if request.method == 'GET':
        try:
            created_by = request.args.get('created_by')
            is_active = request.args.get('is_active')
            status = request.args.get('status')  # draft или ready
            limit = request.args.get('limit', default=100, type=int)
            offset = request.args.get('offset', default=0, type=int)

            if is_active is not None:
                is_active = is_active.lower() == 'true'

            # Если передан status, фильтруем по нему
            if status:
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    query = "SELECT * FROM quiz_stats WHERE status = ?"
                    params = [status]

                    if created_by:
                        query += " AND created_by = ?"
                        params.append(created_by)

                    if is_active is not None:
                        query += " AND is_active = ?"
                        params.append(1 if is_active else 0)

                    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
                    params.extend([limit, offset])

                    cursor.execute(query, params)
                    quizzes = [dict(row) for row in cursor.fetchall()]
            else:
                quizzes = db.get_all_quizzes(
                    created_by=created_by,
                    is_active=is_active,
                    limit=limit,
                    offset=offset
                )

            return jsonify({
                "success": True,
                "quizzes": quizzes,
                "count": len(quizzes)
            })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    elif request.method == 'POST':
        try:
            data = request.get_json()

            if not data or not data.get('title'):
                return jsonify({
                    "success": False,
                    "error": "Необходимо указать title"
                }), 400

            # Создаем викторину
            quiz = db.create_quiz(
                title=data['title'],
                description=data.get('description'),
                created_by=data.get('created_by'),
                question_ids=data.get('question_ids', []),
                time_limit=data.get('time_limit'),
                show_correct_answers=data.get('show_correct_answers', False),
                allow_review=data.get('allow_review', True),
                pass_threshold=data.get('pass_threshold', 0.0),
                shuffle_questions=data.get('shuffle_questions', False),
                shuffle_options=data.get('shuffle_options', False),
                max_attempts=data.get('max_attempts', 1),
                available_from=data.get('available_from'),
                available_until=data.get('available_until')
            )

            return jsonify({
                "success": True,
                "quiz": quiz,
                "message": f"Викторина создана. Код доступа: {quiz['unique_code']}"
            })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


@app.route('/api/quizzes/<int:quiz_id>', methods=['GET', 'PUT', 'DELETE'])
def quiz_detail(quiz_id):
    """
    GET: Получить викторину по ID
    PUT: Обновить викторину
    DELETE: Удалить викторину
    """
    if request.method == 'GET':
        try:
            quiz = db.get_quiz(quiz_id=quiz_id)

            if not quiz:
                return jsonify({
                    "success": False,
                    "error": "Викторина не найдена"
                }), 404

            return jsonify({
                "success": True,
                "quiz": quiz
            })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    elif request.method == 'PUT':
        try:
            data = request.get_json()

            if not data:
                return jsonify({
                    "success": False,
                    "error": "Нет данных для обновления"
                }), 400

            result = db.update_quiz(quiz_id, data)

            if result:
                return jsonify({
                    "success": True,
                    "message": "Викторина обновлена"
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Викторина не найдена"
                }), 404

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    elif request.method == 'DELETE':
        try:
            result = db.delete_quiz(quiz_id)

            if result:
                return jsonify({
                    "success": True,
                    "message": "Викторина удалена"
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Викторина не найдена"
                }), 404

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


@app.route('/api/quizzes/code/<code>', methods=['GET'])
def quiz_by_code(code):
    """Получить викторину по уникальному коду"""
    try:
        quiz = db.get_quiz(unique_code=code)

        if not quiz:
            return jsonify({
                "success": False,
                "error": "Викторина не найдена"
            }), 404

        # Для студентов не показываем правильные ответы до завершения
        if not quiz.get('show_correct_answers'):
            for question in quiz.get('questions', []):
                for option in question.get('options', []):
                    option['is_correct'] = None  # Скрываем правильность

        return jsonify({
            "success": True,
            "quiz": quiz
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/quizzes/<code>/start', methods=['POST'])
def start_quiz(code):
    """
    Начать прохождение викторины

    Body:
        {
            "student_name": "Имя студента",
            "student_email": "email@example.com" (optional)
        }
    """
    try:
        data = request.get_json()

        if not data or not data.get('student_name'):
            return jsonify({
                "success": False,
                "error": "Необходимо указать student_name"
            }), 400

        # Получаем IP адрес
        ip_address = request.remote_addr

        attempt = db.start_quiz_attempt(
            unique_code=code,
            student_name=data['student_name'],
            student_email=data.get('student_email'),
            ip_address=ip_address
        )

        if not attempt:
            return jsonify({
                "success": False,
                "error": "Не удалось начать викторину. Возможно, викторина неактивна или исчерпан лимит попыток"
            }), 400

        return jsonify({
            "success": True,
            "attempt": attempt,
            "session_id": attempt['unique_session_id']
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/quizzes/session/<session_id>/answer', methods=['POST'])
def submit_answer(session_id):
    """
    Отправить ответ на вопрос

    Body:
        {
            "question_id": 123,
            "answer": "текст ответа" или ["вариант 1", "вариант 2"],
            "time_spent": 45 (seconds, optional)
        }
    """
    try:
        data = request.get_json()

        if not data or not data.get('question_id'):
            return jsonify({
                "success": False,
                "error": "Необходимо указать question_id и answer"
            }), 400

        # Преобразуем ответ в JSON строку
        answer = data.get('answer')
        if isinstance(answer, (list, dict)):
            answer = json.dumps(answer, ensure_ascii=False)

        result = db.submit_quiz_answer(
            session_id=session_id,
            question_id=data['question_id'],
            answer=answer,
            time_spent=data.get('time_spent')
        )

        if 'error' in result:
            return jsonify({
                "success": False,
                "error": result['error']
            }), 404

        return jsonify({
            "success": True,
            "result": result
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/quizzes/session/<session_id>/complete', methods=['POST'])
def complete_quiz(session_id):
    """Завершить прохождение викторины"""
    try:
        result = db.complete_quiz_attempt(session_id)

        if 'error' in result:
            return jsonify({
                "success": False,
                "error": result['error']
            }), 404

        return jsonify({
            "success": True,
            "results": result
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/quizzes/<int:quiz_id>/attempts', methods=['GET'])
def quiz_attempts(quiz_id):
    """Получить попытки прохождения викторины"""
    try:
        completed_only = request.args.get('completed_only', 'false').lower() == 'true'
        limit = request.args.get('limit', default=100, type=int)
        offset = request.args.get('offset', default=0, type=int)

        attempts = db.get_quiz_attempts(
            quiz_id=quiz_id,
            completed_only=completed_only,
            limit=limit,
            offset=offset
        )

        return jsonify({
            "success": True,
            "attempts": attempts,
            "count": len(attempts)
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/quizzes/session/<session_id>', methods=['GET'])
def attempt_details(session_id):
    """Получить детальную информацию о попытке"""
    try:
        attempt = db.get_attempt_details(session_id=session_id)

        if not attempt:
            return jsonify({
                "success": False,
                "error": "Попытка не найдена"
            }), 404

        return jsonify({
            "success": True,
            "attempt": attempt
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/quizzes/<int:quiz_id>/questions', methods=['GET', 'POST', 'DELETE'])
def quiz_questions(quiz_id):
    """
    GET: Получить список вопросов викторины
    POST: Добавить вопрос в викторину
    DELETE: Удалить вопрос из викторины
    """
    if request.method == 'GET':
        try:
            # Получаем вопросы викторины
            questions = db.get_quiz_questions(quiz_id)

            if questions is None:
                return jsonify({
                    "success": False,
                    "error": "Викторина не найдена"
                }), 404

            return jsonify({
                "success": True,
                "questions": questions
            })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    elif request.method == 'POST':
        try:
            data = request.get_json()

            if not data or not data.get('question_id'):
                return jsonify({
                    "success": False,
                    "error": "Необходимо указать question_id"
                }), 400

            question_id = data['question_id']

            # Добавляем вопрос в викторину
            success = db.add_question_to_quiz(quiz_id, question_id)

            if success:
                # Получаем обновленную викторину
                quiz = db.get_quiz(quiz_id)
                return jsonify({
                    "success": True,
                    "message": "Вопрос добавлен в викторину",
                    "quiz": quiz
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Не удалось добавить вопрос (викторина не найдена, имеет статус ready, или вопрос уже добавлен)"
                }), 400

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    elif request.method == 'DELETE':
        try:
            data = request.get_json()

            if not data or not data.get('question_id'):
                return jsonify({
                    "success": False,
                    "error": "Необходимо указать question_id"
                }), 400

            question_id = data['question_id']

            # Удаляем вопрос из викторины
            success = db.remove_question_from_quiz(quiz_id, question_id)

            if success:
                # Получаем обновленную викторину
                quiz = db.get_quiz(quiz_id)
                return jsonify({
                    "success": True,
                    "message": "Вопрос удален из викторины",
                    "quiz": quiz
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Не удалось удалить вопрос"
                }), 400

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


@app.route('/api/quizzes/<int:quiz_id>/status', methods=['PATCH'])
def quiz_status(quiz_id):
    """Изменить статус викторины"""
    try:
        data = request.get_json()

        if not data or not data.get('status'):
            return jsonify({
                "success": False,
                "error": "Необходимо указать status"
            }), 400

        status = data['status']

        if status not in ['draft', 'ready']:
            return jsonify({
                "success": False,
                "error": "Статус должен быть 'draft' или 'ready'"
            }), 400

        # Обновляем статус
        success = db.update_quiz_status(quiz_id, status)

        if success:
            # Получаем обновленную викторину
            quiz = db.get_quiz(quiz_id)
            return jsonify({
                "success": True,
                "message": f"Статус викторины изменен на '{status}'",
                "quiz": quiz
            })
        else:
            return jsonify({
                "success": False,
                "error": "Не удалось обновить статус"
            }), 400

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==================== УПРАВЛЕНИЕ PDF ФАЙЛАМИ ====================

@app.route('/api/pdfs', methods=['GET', 'POST'])
def manage_pdfs():
    """
    GET: Получить список PDF файлов с фильтрацией
    POST: Создать новую запись PDF для ручных вопросов

    GET Query params:
        - university: фильтр по университету
        - olympiad: фильтр по олимпиаде
        - year: фильтр по году
        - subject: фильтр по предмету
        - search: поиск по имени или пути
        - limit: количество результатов (по умолчанию 100)
        - offset: смещение для пагинации

    POST Body:
        - display_name: отображаемое имя (обязательно)
        - university: университет
        - olympiad: олимпиада
        - year: год
        - subject: предмет
    """
    if request.method == 'GET':
        try:
            # Получаем параметры фильтрации
            university = request.args.get('university')
            olympiad = request.args.get('olympiad')
            year = request.args.get('year')
            subject = request.args.get('subject')
            search = request.args.get('search')
            limit = int(request.args.get('limit', 100))
            offset = int(request.args.get('offset', 0))

            # Получаем список PDF
            pdfs = db.get_pdfs(
                university=university,
                olympiad=olympiad,
                year=year,
                subject=subject,
                search=search,
                limit=limit,
                offset=offset
            )

            return jsonify({
                "success": True,
                "pdfs": pdfs,
                "count": len(pdfs)
            })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    elif request.method == 'POST':
        try:
            data = request.get_json()

            # Проверяем обязательные поля
            if not data or not data.get('display_name'):
                return jsonify({
                    "success": False,
                    "error": "Поле display_name обязательно"
                }), 400

            # Создаем новую запись PDF
            pdf_id = db.create_pdf_entry(
                display_name=data['display_name'],
                university=data.get('university'),
                olympiad=data.get('olympiad'),
                year=data.get('year'),
                subject=data.get('subject')
            )

            if pdf_id:
                # Получаем созданный PDF
                pdf = db.get_pdf_by_id(pdf_id)
                return jsonify({
                    "success": True,
                    "pdf": pdf
                }), 201
            else:
                return jsonify({
                    "success": False,
                    "error": "Не удалось создать PDF"
                }), 500

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


@app.route('/api/pdfs/<int:pdf_id>', methods=['GET', 'PUT', 'DELETE'])
def pdf_details(pdf_id):
    """
    GET: Получить информацию о конкретном PDF
    PUT: Обновить метаданные PDF
    DELETE: Удалить PDF файл и все связанные вопросы

    PUT Body:
        - display_name: новое отображаемое имя
        - university: университет
        - olympiad: олимпиада
        - year: год
        - subject: предмет
        - cascade_to_questions: обновить теги вопросов (по умолчанию true)
    """
    if request.method == 'GET':
        try:
            pdf = db.get_pdf_by_id(pdf_id)

            if not pdf:
                return jsonify({
                    "success": False,
                    "error": "PDF не найден"
                }), 404

            return jsonify({
                "success": True,
                "pdf": pdf
            })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    elif request.method == 'PUT':
        try:
            data = request.get_json()

            if not data:
                return jsonify({
                    "success": False,
                    "error": "Нет данных для обновления"
                }), 400

            # Обновляем метаданные
            cascade = data.get('cascade_to_questions', True)

            success = db.update_pdf_metadata(
                pdf_id=pdf_id,
                display_name=data.get('display_name'),
                university=data.get('university'),
                olympiad=data.get('olympiad'),
                year=data.get('year'),
                subject=data.get('subject'),
                cascade_to_questions=cascade
            )

            if success:
                # Получаем обновленный PDF
                pdf = db.get_pdf_by_id(pdf_id)
                return jsonify({
                    "success": True,
                    "pdf": pdf
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "PDF не найден или не удалось обновить"
                }), 404

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    elif request.method == 'DELETE':
        try:
            conn = sqlite3.connect('olympiad_questions.db')
            cursor = conn.cursor()

            # Получаем информацию о PDF перед удалением
            cursor.execute("SELECT file_path FROM pdf_files WHERE id = ?", (pdf_id,))
            pdf = cursor.fetchone()

            if not pdf:
                conn.close()
                return jsonify({
                    "success": False,
                    "error": "PDF не найден"
                }), 404

            file_path = pdf[0]

            # Считаем сколько вопросов будет удалено
            cursor.execute("SELECT COUNT(*) FROM questions WHERE source_pdf = ?", (file_path,))
            questions_count = cursor.fetchone()[0]

            # Удаляем все связанные данные
            # ВАЖНО: Сначала удаляем вопросы, чтобы триггеры не блокировали удаление options
            # 1. Удаляем вопросы
            cursor.execute("DELETE FROM questions WHERE source_pdf = ?", (file_path,))

            # 2. Затем очищаем orphaned записи, если они остались
            cursor.execute("""
                DELETE FROM tags WHERE question_id IN (
                    SELECT id FROM questions WHERE source_pdf = ?
                )
            """, (file_path,))

            cursor.execute("""
                DELETE FROM options WHERE question_id IN (
                    SELECT id FROM questions WHERE source_pdf = ?
                )
            """, (file_path,))

            cursor.execute("""
                DELETE FROM matching_pairs WHERE question_id IN (
                    SELECT id FROM questions WHERE source_pdf = ?
                )
            """, (file_path,))

            # 3. Удаляем запись о PDF
            cursor.execute("DELETE FROM pdf_files WHERE id = ?", (pdf_id,))

            conn.commit()
            conn.close()

            return jsonify({
                "success": True,
                "message": "PDF файл и связанные вопросы удалены",
                "questions_deleted": questions_count
            })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


# ============================================================================
# НАСТРОЙКИ
# ============================================================================

@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Получить все настройки"""
    try:
        conn = db.conn
        cursor = conn.cursor()

        cursor.execute("""
            SELECT key, value, description, updated_at
            FROM settings
            ORDER BY key
        """)

        settings = {}
        for row in cursor.fetchall():
            settings[row[0]] = {
                "value": row[1],
                "description": row[2],
                "updated_at": row[3]
            }

        return jsonify({
            "success": True,
            "settings": settings
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/settings/<key>', methods=['GET', 'PUT'])
def manage_setting(key):
    """
    GET: Получить конкретную настройку
    PUT: Обновить настройку

    PUT Body:
        {
            "value": "новое значение"
        }
    """
    if request.method == 'GET':
        try:
            conn = db.conn
            cursor = conn.cursor()

            cursor.execute("""
                SELECT value, description, updated_at
                FROM settings
                WHERE key = ?
            """, (key,))

            result = cursor.fetchone()

            if not result:
                return jsonify({
                    "success": False,
                    "error": "Настройка не найдена"
                }), 404

            return jsonify({
                "success": True,
                "key": key,
                "value": result[0],
                "description": result[1],
                "updated_at": result[2]
            })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    elif request.method == 'PUT':
        try:
            data = request.get_json()

            if not data or 'value' not in data:
                return jsonify({
                    "success": False,
                    "error": "Необходимо указать value"
                }), 400

            conn = db.conn
            cursor = conn.cursor()

            # Обновляем или создаем настройку
            cursor.execute("""
                INSERT INTO settings (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = CURRENT_TIMESTAMP
            """, (key, data['value']))

            conn.commit()

            return jsonify({
                "success": True,
                "key": key,
                "value": data['value'],
                "message": "Настройка обновлена"
            })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


# ============================================================================
# АДМИНИСТРАТИВНЫЕ ЭНДПОИНТЫ
# ============================================================================

@app.route('/api/admin/backup', methods=['POST'])
def admin_backup():
    """Создание бэкапа базы данных"""
    try:
        import subprocess
        from pathlib import Path
        from datetime import datetime

        # Запуск скрипта бэкапа
        result = subprocess.run(
            ['./backup_db.sh'],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            # Извлекаем имя файла из вывода
            output_lines = result.stdout.strip().split('\n')
            backup_file = None
            for line in output_lines:
                if 'olympiad_questions_' in line and '.db' in line:
                    backup_file = line.split(': ')[-1]
                    break

            return jsonify({
                "success": True,
                "message": "Бэкап успешно создан",
                "backup_file": backup_file,
                "timestamp": datetime.now().isoformat(),
                "output": result.stdout
            })
        else:
            return jsonify({
                "success": False,
                "error": "Ошибка при создании бэкапа",
                "output": result.stderr
            }), 500

    except subprocess.TimeoutExpired:
        return jsonify({
            "success": False,
            "error": "Таймаут при создании бэкапа"
        }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/admin/sync-db', methods=['POST'])
def admin_sync_db():
    """Синхронизация БД между корнем и api/"""
    try:
        import subprocess
        from pathlib import Path
        from datetime import datetime

        # Запуск скрипта синхронизации
        result = subprocess.run(
            ['./sync_db.sh'],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            return jsonify({
                "success": True,
                "message": "Синхронизация выполнена",
                "timestamp": datetime.now().isoformat(),
                "output": result.stdout
            })
        else:
            return jsonify({
                "success": False,
                "error": "Ошибка при синхронизации",
                "output": result.stderr
            }), 500

    except subprocess.TimeoutExpired:
        return jsonify({
            "success": False,
            "error": "Таймаут при синхронизации"
        }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================================
# ЭНДПОИНТЫ ДЛЯ РАБОТЫ С ПРОВЕРКОЙ ВОПРОСОВ
# ============================================================================

@app.route('/api/questions/<int:question_id>/verify', methods=['PUT'])
def verify_question(question_id):
    """Пометить вопрос как проверенный"""
    try:
        data = request.get_json()
        verified = data.get('verified', True)
        verified_by = data.get('verified_by', 'system')

        conn = db.conn
        cursor = conn.cursor()

        if verified:
            cursor.execute("""
                UPDATE questions
                SET verified = 1,
                    verified_at = CURRENT_TIMESTAMP,
                    verified_by = ?
                WHERE id = ?
            """, (verified_by, question_id))
        else:
            cursor.execute("""
                UPDATE questions
                SET verified = 0,
                    verified_at = NULL,
                    verified_by = NULL
                WHERE id = ?
            """, (question_id,))

        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({
                "success": False,
                "error": "Вопрос не найден"
            }), 404

        # Получаем обновленный вопрос
        question = db.get_question_by_id(question_id)

        # Триггер автоматически обновит verification_status у PDF,
        # но получим актуальную информацию
        if question and question.get('source_pdf'):
            cursor.execute("""
                SELECT verification_status
                FROM pdf_files
                WHERE file_path = ?
            """, (question['source_pdf'],))
            result = cursor.fetchone()
            pdf_status = result[0] if result else None
        else:
            pdf_status = None

        return jsonify({
            "success": True,
            "question": question,
            "pdf_verification_status": pdf_status
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/questions/bulk-verify', methods=['POST'])
def bulk_verify_questions():
    """Массовая проверка вопросов"""
    try:
        data = request.get_json()
        question_ids = data.get('question_ids', [])
        verified_by = data.get('verified_by', 'system')

        if not question_ids:
            return jsonify({
                "success": False,
                "error": "Не указаны ID вопросов"
            }), 400

        conn = db.conn
        cursor = conn.cursor()

        # Обновляем все вопросы
        placeholders = ','.join('?' * len(question_ids))
        cursor.execute(f"""
            UPDATE questions
            SET verified = 1,
                verified_at = CURRENT_TIMESTAMP,
                verified_by = ?
            WHERE id IN ({placeholders})
        """, [verified_by] + question_ids)

        conn.commit()
        updated_count = cursor.rowcount

        return jsonify({
            "success": True,
            "updated_count": updated_count,
            "question_ids": question_ids
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================================
# РАСШИРЕННЫЕ ЭНДПОИНТЫ ДЛЯ PDF ФАЙЛОВ
# ============================================================================

@app.route('/api/pdfs/<int:pdf_id>/verification-stats', methods=['GET'])
def get_pdf_verification_stats(pdf_id):
    """Получить статистику проверки вопросов в файле"""
    try:
        # Получаем информацию о PDF
        pdf = db.get_pdf_by_id(pdf_id)
        if not pdf:
            return jsonify({
                "success": False,
                "error": "PDF не найден"
            }), 404

        conn = db.conn
        cursor = conn.cursor()

        # Общее количество вопросов
        cursor.execute("""
            SELECT COUNT(*) FROM questions WHERE source_pdf = ?
        """, (pdf['file_path'],))
        total = cursor.fetchone()[0]

        # Проверенные вопросы
        cursor.execute("""
            SELECT COUNT(*) FROM questions
            WHERE source_pdf = ? AND verified = 1
        """, (pdf['file_path'],))
        verified = cursor.fetchone()[0]

        unverified = total - verified

        # Автоматический расчет статуса
        if total == 0:
            auto_status = 'not_verified'
        elif verified == total:
            auto_status = 'verified'
        elif verified > 0:
            auto_status = 'partially_verified'
        else:
            auto_status = 'not_verified'

        return jsonify({
            "success": True,
            "pdf_id": pdf_id,
            "stats": {
                "total": total,
                "verified": verified,
                "unverified": unverified,
                "auto_status": auto_status,
                "current_status": pdf.get('verification_status', 'not_verified'),
                "is_manual_override": bool(pdf.get('manual_verification_override', False))
            }
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/pdfs/<int:pdf_id>/verification-status', methods=['PUT'])
def update_pdf_verification_status(pdf_id):
    """Обновить статус проверки файла (ручное переопределение)"""
    try:
        data = request.get_json()
        status = data.get('status')

        if status not in ['verified', 'partially_verified', 'not_verified']:
            return jsonify({
                "success": False,
                "error": "Неверный статус. Допустимые значения: verified, partially_verified, not_verified"
            }), 400

        conn = db.conn
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE pdf_files
            SET verification_status = ?,
                manual_verification_override = 1
            WHERE id = ?
        """, (status, pdf_id))

        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({
                "success": False,
                "error": "PDF не найден"
            }), 404

        # Получаем обновленный PDF
        pdf = db.get_pdf_by_id(pdf_id)

        return jsonify({
            "success": True,
            "pdf": pdf
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/pdfs/upload', methods=['POST'])
def upload_pdf():
    """Загрузка нового PDF файла с автоматическим парсингом"""
    try:
        import hashlib
        import os
        from datetime import datetime
        from werkzeug.utils import secure_filename
        from pathlib import Path

        # Проверка наличия файла
        if 'file' not in request.files:
            return jsonify({
                "success": False,
                "error": "Файл не предоставлен"
            }), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({
                "success": False,
                "error": "Имя файла пустое"
            }), 400

        # Проверка типа файла
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({
                "success": False,
                "error": "Разрешены только PDF файлы"
            }), 400

        # Получаем метаданные из формы
        display_name = request.form.get('display_name', file.filename)
        university = request.form.get('university', '')
        olympiad = request.form.get('olympiad', '')
        subject = request.form.get('subject', '')
        year = request.form.get('year', '')
        file_type = request.form.get('file_type', 'olympiad')
        difficulty = request.form.get('difficulty', type=int)
        download_source = request.form.get('download_source', '')

        # Создаем директорию для ручных загрузок
        upload_dir = Path(__file__).parent.parent / 'olympiads' / 'manual'
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Безопасное имя файла
        filename = secure_filename(file.filename)
        file_path = upload_dir / filename

        # Если файл с таким именем существует, добавляем timestamp
        if file_path.exists():
            name, ext = os.path.splitext(filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{name}_{timestamp}{ext}"
            file_path = upload_dir / filename

        # Сохраняем файл
        file.save(str(file_path))

        # Вычисляем SHA256
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        file_hash = sha256_hash.hexdigest()

        # Проверяем дубликаты
        conn = db.conn
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, file_path, display_name
            FROM pdf_files
            WHERE file_hash = ?
        """, (file_hash,))
        duplicate = cursor.fetchone()

        if duplicate:
            # Удаляем загруженный файл
            os.remove(file_path)

            return jsonify({
                "success": False,
                "error": "duplicate",
                "message": "Файл с таким содержимым уже существует",
                "existing_file": {
                    "id": duplicate[0],
                    "file_path": duplicate[1],
                    "display_name": duplicate[2]
                }
            }), 409

        # Относительный путь для БД
        relative_path = f"olympiads/manual/{filename}"

        # Сохраняем метаданные в БД
        # is_manual = 1 потому что файл загружен через веб-интерфейс вручную
        cursor.execute("""
            INSERT INTO pdf_files (
                file_path, display_name, university, olympiad, year, subject,
                file_type, difficulty, file_hash, download_source,
                is_manual, verification_status, last_parsed_at, parser_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 'not_verified', CURRENT_TIMESTAMP, '1.0.0')
        """, (
            relative_path, display_name, university, olympiad, year, subject,
            file_type, difficulty, file_hash, download_source
        ))

        pdf_id = cursor.lastrowid
        conn.commit()

        # Парсинг файла
        try:
            from parsers.pdf_parser import PDFParser
            parser = PDFParser()
            questions = parser.parse_pdf(str(file_path))

            # Сохраняем вопросы
            questions_saved = 0
            for q in questions:
                q['source_pdf'] = relative_path
                question_id = db.save_question(q)
                if question_id:
                    questions_saved += 1

            # Обновляем количество вопросов
            cursor.execute("""
                UPDATE pdf_files
                SET question_count = ?
                WHERE id = ?
            """, (questions_saved, pdf_id))
            conn.commit()

            return jsonify({
                "success": True,
                "pdf_id": pdf_id,
                "file_path": relative_path,
                "file_hash": file_hash,
                "questions_parsed": questions_saved,
                "message": f"Файл загружен и распарсен. Найдено {questions_saved} вопросов"
            })

        except Exception as parse_error:
            # Парсинг не удался, но файл сохранен
            return jsonify({
                "success": True,
                "pdf_id": pdf_id,
                "file_path": relative_path,
                "file_hash": file_hash,
                "questions_parsed": 0,
                "warning": f"Файл сохранен, но парсинг не удался: {str(parse_error)}"
            })

    except Exception as e:
        # Удаляем файл если что-то пошло не так
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/pdfs/<int:pdf_id>/reparse', methods=['POST'])
def reparse_pdf(pdf_id):
    """Перепарсить PDF файл (возвращает превью без сохранения)"""
    try:
        from pathlib import Path

        # Получаем информацию о PDF
        pdf = db.get_pdf_by_id(pdf_id)
        if not pdf:
            return jsonify({
                "success": False,
                "error": "PDF не найден"
            }), 404

        file_path = Path(__file__).parent.parent / pdf['file_path']

        if not file_path.exists():
            return jsonify({
                "success": False,
                "error": "Физический файл не найден"
            }), 404

        # Парсим файл
        from parsers.pdf_parser import PDFParser
        parser = PDFParser()
        questions = parser.parse_pdf(str(file_path))

        # Получаем существующие вопросы
        conn = db.conn
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, text FROM questions WHERE source_pdf = ?
        """, (pdf['file_path'],))
        existing_questions = cursor.fetchall()

        return jsonify({
            "success": True,
            "preview": {
                "questions_found": len(questions),
                "questions": questions[:10],  # Первые 10 для превью
                "existing_questions_count": len(existing_questions),
                "total_questions": len(questions)
            },
            "message": f"Найдено {len(questions)} вопросов. Сейчас в БД: {len(existing_questions)}"
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/pdfs/<int:pdf_id>/apply-reparse', methods=['POST'])
def apply_reparse(pdf_id):
    """Применить результаты перепарсинга"""
    try:
        from pathlib import Path

        data = request.get_json()
        strategy = data.get('strategy', 'add_new')  # 'replace_all' или 'add_new'

        # Получаем информацию о PDF
        pdf = db.get_pdf_by_id(pdf_id)
        if not pdf:
            return jsonify({
                "success": False,
                "error": "PDF не найден"
            }), 404

        file_path = Path(__file__).parent.parent / pdf['file_path']

        if not file_path.exists():
            return jsonify({
                "success": False,
                "error": "Физический файл не найден"
            }), 404

        conn = db.conn
        cursor = conn.cursor()

        # Если заменяем все - удаляем старые вопросы
        if strategy == 'replace_all':
            cursor.execute("""
                DELETE FROM questions WHERE source_pdf = ?
            """, (pdf['file_path'],))
            conn.commit()

        # Парсим и сохраняем
        from parsers.pdf_parser import PDFParser
        parser = PDFParser()
        questions = parser.parse_pdf(str(file_path))

        questions_saved = 0
        for q in questions:
            q['source_pdf'] = pdf['file_path']
            question_id = db.save_question(q)
            if question_id:
                questions_saved += 1

        # Обновляем метаданные PDF
        cursor.execute("""
            UPDATE pdf_files
            SET question_count = ?,
                last_parsed_at = CURRENT_TIMESTAMP,
                parser_version = '1.0.0'
            WHERE id = ?
        """, (questions_saved, pdf_id))
        conn.commit()

        return jsonify({
            "success": True,
            "questions_added": questions_saved,
            "strategy": strategy,
            "message": f"Сохранено {questions_saved} вопросов"
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==================== ПРОСМОТР PDF ФАЙЛОВ ====================

@app.route('/api/pdf/<path:file_path>', methods=['GET', 'HEAD'])
def view_pdf(file_path):
    """
    Отдать PDF файл для просмотра

    Args:
        file_path: Относительный путь к PDF файлу

    Returns:
        PDF файл
    """
    try:
        import os
        from urllib.parse import unquote
        from pathlib import Path

        # Декодируем путь
        file_path = unquote(file_path)

        # Пробуем разные варианты базовых директорий
        base_dirs = [
            Path(__file__).parent.parent,  # Корень проекта
            Path.cwd(),  # Текущая директория
        ]

        full_path = None
        for base_dir in base_dirs:
            test_path = base_dir / file_path
            if test_path.exists():
                full_path = test_path
                break

        # Если не нашли, пробуем как абсолютный путь
        if not full_path and os.path.exists(file_path):
            full_path = Path(file_path)

        if not full_path or not full_path.exists():
            # Provide helpful error message for debugging
            searched_paths = [str(base_dir / file_path) for base_dir in base_dirs]
            return jsonify({
                "success": False,
                "error": "PDF файл не найден",
                "message": "Файл отсутствует в файловой системе. Возможно, он был удалён или не был загружен.",
                "requested_path": file_path,
                "searched_locations": searched_paths
            }), 404

        # Отдаем файл
        return send_file(
            str(full_path),
            mimetype='application/pdf',
            as_attachment=False,  # Открыть в браузере, а не скачать
            download_name=full_path.name
        )

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Ошибка при открытии PDF: {str(e)}"
        }), 500


# ==================== ЗАГРУЗЧИК ИЗ СЕТИ ====================

# Путь к конфигурации загрузчика
DOWNLOADER_SCRIPT = Path(__file__).parent.parent / 'olympiad_downloader.py'
DOWNLOADER_DB = Path(__file__).parent.parent / 'olympiads' / 'database.json'
DOWNLOADER_LOGS_DIR = Path(__file__).parent.parent / 'olympiads' / 'logs'

@app.route('/api/downloader/sources', methods=['GET'])
def get_downloader_sources():
    """Получить список источников загрузки"""
    try:
        # Читаем конфигурацию из olympiad_downloader.py
        import importlib.util
        spec = importlib.util.spec_from_file_location("downloader", DOWNLOADER_SCRIPT)
        downloader = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(downloader)

        sources = downloader.OLYMPIAD_SOURCES

        return jsonify({
            "success": True,
            "sources": sources
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/downloader/sources', methods=['POST'])
def add_downloader_source():
    """Добавить новый источник загрузки"""
    try:
        data = request.get_json()
        name = data.get('name')
        config = data.get('config')

        if not name or not config:
            return jsonify({
                "success": False,
                "error": "Необходимо указать name и config"
            }), 400

        # Читаем файл olympiad_downloader.py
        with open(DOWNLOADER_SCRIPT, 'r', encoding='utf-8') as f:
            content = f.read()

        # Находим OLYMPIAD_SOURCES
        import re
        pattern = r'(OLYMPIAD_SOURCES = \{)(.*?)(\n\})'
        match = re.search(pattern, content, re.DOTALL)

        if not match:
            return jsonify({
                "success": False,
                "error": "Не удалось найти OLYMPIAD_SOURCES в файле"
            }), 500

        # Формируем новую запись
        urls_str = ',\n            '.join([f'"{url}"' for url in config['urls']])
        new_entry = f'''    "{name}": {{
        "urls": [
            {urls_str}
        ],
        "type": "{config['type']}"
    }},'''

        # Вставляем новую запись
        new_sources = match.group(1) + '\n' + new_entry + match.group(2) + match.group(3)
        new_content = content[:match.start()] + new_sources + content[match.end():]

        # Сохраняем файл
        with open(DOWNLOADER_SCRIPT, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return jsonify({
            "success": True,
            "message": f"Источник {name} успешно добавлен"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/downloader/sources/<source_name>', methods=['PUT'])
def update_downloader_source(source_name):
    """Обновить источник загрузки"""
    try:
        data = request.get_json()
        urls = data.get('urls', [])
        source_type = data.get('type', 'selenium')

        # Читаем файл
        with open(DOWNLOADER_SCRIPT, 'r', encoding='utf-8') as f:
            content = f.read()

        # Находим и обновляем конкретный источник
        import re
        # Ищем источник по имени
        pattern = rf'("{source_name}": \{{)(.*?)(\n    \}},)'
        match = re.search(pattern, content, re.DOTALL)

        if not match:
            return jsonify({
                "success": False,
                "error": f"Источник {source_name} не найден"
            }), 404

        # Формируем новую конфигурацию
        urls_str = ',\n            '.join([f'"{url}"' for url in urls])
        new_config = f'''"urls": [
            {urls_str}
        ],
        "type": "{source_type}"'''

        new_entry = match.group(1) + '\n        ' + new_config + match.group(3)
        new_content = content[:match.start()] + new_entry + content[match.end():]

        # Сохраняем
        with open(DOWNLOADER_SCRIPT, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return jsonify({
            "success": True,
            "message": f"Источник {source_name} обновлён"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/downloader/sources/<source_name>', methods=['DELETE'])
def delete_downloader_source(source_name):
    """Удалить источник загрузки"""
    try:
        # Читаем файл
        with open(DOWNLOADER_SCRIPT, 'r', encoding='utf-8') as f:
            content = f.read()

        # Находим и удаляем источник
        import re
        pattern = rf'    "{source_name}": \{{.*?\n    \}},\n'
        new_content = re.sub(pattern, '', content, flags=re.DOTALL)

        if new_content == content:
            return jsonify({
                "success": False,
                "error": f"Источник {source_name} не найден"
            }), 404

        # Сохраняем
        with open(DOWNLOADER_SCRIPT, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return jsonify({
            "success": True,
            "message": f"Источник {source_name} удалён"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/downloader/start', methods=['POST'])
def start_downloader():
    """Запустить загрузчик"""
    try:
        data = request.get_json()
        mode = data.get('mode', 'update')  # update, full, dry

        # Формируем команду
        cmd = ['python3', str(DOWNLOADER_SCRIPT)]

        if mode == 'full':
            cmd.append('--full')
        elif mode == 'dry':
            cmd.append('--dry')
        else:
            cmd.append('--update')

        # Запускаем в фоне
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(DOWNLOADER_SCRIPT.parent)
        )

        return jsonify({
            "success": True,
            "message": f"Загрузчик запущен в режиме {mode}",
            "pid": process.pid
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/downloader/logs', methods=['GET'])
def get_downloader_logs():
    """Получить логи загрузчика"""
    try:
        # Находим последний лог файл
        DOWNLOADER_LOGS_DIR.mkdir(parents=True, exist_ok=True)
        log_files = sorted(DOWNLOADER_LOGS_DIR.glob('download_*.log'), key=lambda x: x.stat().st_mtime, reverse=True)

        if not log_files:
            return jsonify({
                "success": True,
                "logs": []
            })

        # Читаем последний лог
        latest_log = log_files[0]
        with open(latest_log, 'r', encoding='utf-8') as f:
            logs = f.readlines()

        # Ограничиваем до последних 100 строк
        logs = logs[-100:]

        return jsonify({
            "success": True,
            "logs": [line.strip() for line in logs],
            "log_file": latest_log.name
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/downloader/stats', methods=['GET'])
def get_downloader_stats():
    """Получить статистику загрузчика"""
    try:
        if not DOWNLOADER_DB.exists():
            return jsonify({
                "success": True,
                "stats": {
                    "total_files": 0,
                    "last_update": None,
                    "by_source": {}
                }
            })

        # Читаем базу данных загрузчика
        with open(DOWNLOADER_DB, 'r', encoding='utf-8') as f:
            db_data = json.load(f)

        # Подсчитываем статистику
        total_files = len(db_data.get('files', {}))
        last_update = db_data.get('last_update')

        # Статистика по источникам
        by_source = {}
        for file_info in db_data.get('files', {}).values():
            org = file_info.get('organizer', 'unknown')
            by_source[org] = by_source.get(org, 0) + 1

        return jsonify({
            "success": True,
            "stats": {
                "total_files": total_files,
                "last_update": last_update,
                "by_source": by_source
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/downloader/subjects', methods=['GET'])
def get_subjects():
    """Получить список предметов для поиска"""
    try:
        # Читаем конфигурацию из olympiad_downloader.py
        import importlib.util
        spec = importlib.util.spec_from_file_location("downloader", DOWNLOADER_SCRIPT)
        downloader = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(downloader)

        subjects = downloader.SUBJECTS

        return jsonify({
            "success": True,
            "subjects": subjects
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/downloader/subjects', methods=['POST'])
def add_subject():
    """Добавить новый предмет для поиска"""
    try:
        data = request.get_json()
        subject = data.get('subject', '').strip().lower()

        if not subject:
            return jsonify({
                "success": False,
                "error": "Необходимо указать название предмета"
            }), 400

        # Читаем файл olympiad_downloader.py
        with open(DOWNLOADER_SCRIPT, 'r', encoding='utf-8') as f:
            content = f.read()

        # Находим SUBJECTS
        import re
        pattern = r'(SUBJECTS = \[)(.*?)(\n\])'
        match = re.search(pattern, content, re.DOTALL)

        if not match:
            return jsonify({
                "success": False,
                "error": "Не удалось найти SUBJECTS в файле"
            }), 500

        # Проверяем, что предмет еще не добавлен
        current_subjects = match.group(2)
        if f'"{subject}"' in current_subjects:
            return jsonify({
                "success": False,
                "error": f"Предмет '{subject}' уже существует"
            }), 400

        # Добавляем новый предмет в конец списка (перед последней запятой если она есть)
        subjects_part = match.group(2).rstrip()
        if subjects_part and not subjects_part.endswith(','):
            subjects_part += ','

        new_subjects = subjects_part + f'\n    "{subject}"'
        new_content = content[:match.start()] + match.group(1) + new_subjects + match.group(3) + content[match.end():]

        # Сохраняем файл
        with open(DOWNLOADER_SCRIPT, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return jsonify({
            "success": True,
            "message": f"Предмет '{subject}' успешно добавлен"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/downloader/subjects/<subject>', methods=['DELETE'])
def delete_subject(subject):
    """Удалить предмет из поиска"""
    try:
        # Читаем файл
        with open(DOWNLOADER_SCRIPT, 'r', encoding='utf-8') as f:
            content = f.read()

        # Находим и удаляем предмет
        import re
        # Ищем строку с предметом (с учетом кавычек и возможной запятой)
        patterns = [
            rf',?\s*"{subject}",?\s*\n',  # Предмет на отдельной строке
            rf',\s*"{subject}"',          # Предмет в конце списка
            rf'"{subject}",\s*',          # Предмет в начале/середине списка
        ]

        original_content = content
        for pattern in patterns:
            content = re.sub(pattern, '', content)
            if content != original_content:
                break

        if content == original_content:
            return jsonify({
                "success": False,
                "error": f"Предмет '{subject}' не найден"
            }), 404

        # Сохраняем
        with open(DOWNLOADER_SCRIPT, 'w', encoding='utf-8') as f:
            f.write(content)

        return jsonify({
            "success": True,
            "message": f"Предмет '{subject}' удалён"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/images/upload', methods=['POST'])
def upload_image():
    """
    Загрузить изображение

    Form data:
        - file: файл изображения
        - question_id: ID вопроса (опционально)
        - option_id: ID варианта ответа (опционально)
        - image_type: тип изображения (опционально)
        - description: описание (опционально)
    """
    try:
        from werkzeug.utils import secure_filename
        from PIL import Image

        if 'file' not in request.files:
            return jsonify({
                "success": False,
                "error": "Файл не предоставлен"
            }), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({
                "success": False,
                "error": "Файл не выбран"
            }), 400

        # Проверяем тип файла
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

        if file_ext not in allowed_extensions:
            return jsonify({
                "success": False,
                "error": f"Недопустимый тип файла. Разрешены: {', '.join(allowed_extensions)}"
            }), 400

        # Получаем параметры
        question_id = request.form.get('question_id', type=int)
        option_id = request.form.get('option_id', type=int)
        matching_pair_id = request.form.get('matching_pair_id', type=int)
        matching_side = request.form.get('matching_side', '')
        image_type = request.form.get('image_type', 'other')
        description = request.form.get('description', '')

        # Определяем директорию для сохранения
        if option_id:
            upload_dir = Path(__file__).parent.parent / 'uploads' / 'option_images'
        elif matching_pair_id:
            upload_dir = Path(__file__).parent.parent / 'uploads' / 'matching_images'
        else:
            upload_dir = Path(__file__).parent.parent / 'uploads' / 'question_images'

        upload_dir.mkdir(parents=True, exist_ok=True)

        # Генерируем уникальное имя файла
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        file_path = upload_dir / unique_filename

        # Сохраняем файл
        file.save(str(file_path))

        # Получаем размеры изображения (если это не SVG)
        width, height = None, None
        if file_ext != 'svg':
            try:
                with Image.open(file_path) as img:
                    width, height = img.size
            except Exception:
                pass

        # Относительный путь для БД
        if option_id:
            relative_path = f"uploads/option_images/{unique_filename}"
        elif matching_pair_id:
            relative_path = f"uploads/matching_images/{unique_filename}"
        else:
            relative_path = f"uploads/question_images/{unique_filename}"

        # Сохраняем в БД
        conn = db.conn
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO images (
                question_id, option_id, matching_pair_id, matching_side,
                file_path, image_type, width, height, description
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (question_id, option_id, matching_pair_id, matching_side,
              relative_path, image_type, width, height, description))

        image_id = cursor.lastrowid
        conn.commit()

        return jsonify({
            "success": True,
            "id": image_id,
            "image_id": image_id,
            "question_id": question_id,
            "option_id": option_id,
            "file_path": relative_path,
            "image_type": image_type,
            "width": width,
            "height": height,
            "description": description,
            "message": "Изображение успешно загружено"
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/images/<path:filename>', methods=['GET'])
def get_image(filename):
    """Получить изображение по пути"""
    try:
        # Базовая директория для изображений
        base_dir = Path(__file__).parent.parent
        file_path = base_dir / filename

        # Проверяем, что файл существует и находится в разрешенной директории
        if not file_path.exists():
            return jsonify({
                "success": False,
                "error": "Файл не найден"
            }), 404

        # Проверяем, что путь начинается с uploads/
        try:
            file_path.relative_to(base_dir / 'uploads')
        except ValueError:
            return jsonify({
                "success": False,
                "error": "Доступ запрещен"
            }), 403

        return send_file(str(file_path))

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/images/<int:image_id>', methods=['DELETE'])
def delete_image(image_id):
    """Удалить изображение"""
    try:
        conn = db.conn
        cursor = conn.cursor()

        # Получаем информацию об изображении
        cursor.execute("SELECT file_path FROM images WHERE id = ?", (image_id,))
        result = cursor.fetchone()

        if not result:
            return jsonify({
                "success": False,
                "error": "Изображение не найдено"
            }), 404

        file_path = result[0]

        # Удаляем из БД
        cursor.execute("DELETE FROM images WHERE id = ?", (image_id,))
        conn.commit()

        # Удаляем файл
        full_path = Path(__file__).parent.parent / file_path
        if full_path.exists():
            os.remove(full_path)

        return jsonify({
            "success": True,
            "message": "Изображение удалено"
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/questions/<int:question_id>/images', methods=['GET'])
def get_question_images(question_id):
    """Получить все изображения вопроса"""
    try:
        conn = db.conn
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, file_path, image_type, width, height, description, position
            FROM images
            WHERE question_id = ? AND option_id IS NULL
            ORDER BY position, id
        """, (question_id,))

        images = []
        for row in cursor.fetchall():
            images.append({
                "id": row[0],
                "file_path": row[1],
                "image_type": row[2],
                "width": row[3],
                "height": row[4],
                "description": row[5],
                "position": row[6]
            })

        return jsonify({
            "success": True,
            "images": images
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/options/<int:option_id>/images', methods=['GET'])
def get_option_images(option_id):
    """Получить все изображения варианта ответа"""
    try:
        conn = db.conn
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, file_path, image_type, width, height, description, position
            FROM images
            WHERE option_id = ?
            ORDER BY position, id
        """, (option_id,))

        images = []
        for row in cursor.fetchall():
            images.append({
                "id": row[0],
                "file_path": row[1],
                "image_type": row[2],
                "width": row[3],
                "height": row[4],
                "description": row[5],
                "position": row[6]
            })

        return jsonify({
            "success": True,
            "images": images
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/matching_pairs/<int:pair_id>/images', methods=['GET'])
def get_matching_pair_images(pair_id):
    """Получить все изображения пары соответствия"""
    try:
        conn = db.conn
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, file_path, matching_side, image_type, width, height, description, position
            FROM images
            WHERE matching_pair_id = ?
            ORDER BY matching_side, position, id
        """, (pair_id,))

        images = []
        for row in cursor.fetchall():
            images.append({
                "id": row[0],
                "file_path": row[1],
                "matching_side": row[2],
                "image_type": row[3],
                "width": row[4],
                "height": row[5],
                "description": row[6],
                "position": row[7]
            })

        return jsonify({
            "success": True,
            "images": images
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==================== АВТОТЕСТЫ ====================

@app.route('/api/tests/run', methods=['POST'])
def run_tests():
    """
    Запустить автотесты Playwright

    Body:
        - test_group: группа тестов (@create, @read, @update, @delete, @scoring) или "all"
        - headed: запустить с отображением браузера (true/false)
    """
    try:
        data = request.get_json() or {}
        test_group = data.get('test_group', 'all')
        headed = data.get('headed', False)

        # Базовая директория проекта
        project_dir = Path(__file__).parent.parent

        # Формируем команду
        cmd_parts = ['npx', 'playwright', 'test']

        # Добавляем фильтр по группе
        if test_group and test_group != 'all':
            cmd_parts.extend(['--grep', f'@{test_group}'])

        # Добавляем headed mode если нужно
        if headed:
            cmd_parts.append('--headed')

        # Добавляем JSON reporter
        cmd_parts.extend(['--reporter=json'])

        # Запускаем тесты
        process = subprocess.Popen(
            cmd_parts,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(project_dir),
            text=True
        )

        stdout, stderr = process.communicate(timeout=300)  # 5 минут таймаут

        # Парсим результаты
        results = {
            "success": process.returncode == 0,
            "exit_code": process.returncode,
            "stdout": stdout,
            "stderr": stderr,
        }

        # Пытаемся прочитать JSON отчет
        results_file = project_dir / 'test-results' / 'results.json'
        if results_file.exists():
            try:
                with open(results_file, 'r') as f:
                    import json
                    test_results = json.load(f)
                    results['test_results'] = test_results
            except:
                pass

        return jsonify(results)

    except subprocess.TimeoutExpired:
        return jsonify({
            "success": False,
            "error": "Тесты превысили лимит времени выполнения (5 минут)"
        }), 408
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/tests/cleanup', methods=['POST'])
def cleanup_test_data():
    """
    Очистить все тестовые данные из базы данных

    Удаляет все викторины, вопросы, изображения с префиксом [TEST]
    """
    try:
        TEST_PREFIX = '[TEST]'
        conn = db.conn
        cursor = conn.cursor()

        stats = {
            "quizzes": 0,
            "questions": 0,
            "pdfs": 0,
            "images": 0,
            "errors": []
        }

        # 1. Удаляем тестовые викторины
        cursor.execute("""
            SELECT id, title FROM quizzes
            WHERE title LIKE ?
        """, (f'%{TEST_PREFIX}%',))

        test_quizzes = cursor.fetchall()
        for quiz_id, title in test_quizzes:
            try:
                cursor.execute("DELETE FROM quizzes WHERE id = ?", (quiz_id,))
                stats["quizzes"] += 1
            except Exception as e:
                stats["errors"].append(f"Quiz {quiz_id}: {str(e)}")

        # 2. Удаляем тестовые вопросы
        cursor.execute("""
            SELECT id, text FROM questions
            WHERE text LIKE ?
        """, (f'%{TEST_PREFIX}%',))

        test_questions = cursor.fetchall()
        for question_id, text in test_questions:
            try:
                cursor.execute("DELETE FROM questions WHERE id = ?", (question_id,))
                stats["questions"] += 1
            except Exception as e:
                stats["errors"].append(f"Question {question_id}: {str(e)}")

        # 3. Удаляем тестовые PDF
        cursor.execute("""
            SELECT id, display_name FROM pdf_files
            WHERE display_name LIKE ?
        """, (f'%{TEST_PREFIX}%',))

        test_pdfs = cursor.fetchall()
        for pdf_id, name in test_pdfs:
            try:
                cursor.execute("DELETE FROM pdf_files WHERE id = ?", (pdf_id,))
                stats["pdfs"] += 1
            except Exception as e:
                stats["errors"].append(f"PDF {pdf_id}: {str(e)}")

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Тестовые данные очищены",
            "stats": stats
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/tests/status', methods=['GET'])
def get_test_status():
    """
    Получить статус автотестов

    Возвращает информацию о последнем запуске тестов
    """
    try:
        project_dir = Path(__file__).parent.parent
        results_file = project_dir / 'test-results' / 'results.json'

        if not results_file.exists():
            return jsonify({
                "success": True,
                "has_results": False,
                "message": "Тесты еще не запускались"
            })

        # Читаем результаты
        with open(results_file, 'r') as f:
            import json
            results = json.load(f)

        # Подсчитываем статистику
        stats = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0
        }

        if 'suites' in results:
            for suite in results['suites']:
                for spec in suite.get('specs', []):
                    stats["total"] += 1
                    if spec.get('ok'):
                        stats["passed"] += 1
                    elif any(test.get('status') == 'skipped' for test in spec.get('tests', [])):
                        stats["skipped"] += 1
                    else:
                        stats["failed"] += 1

        return jsonify({
            "success": True,
            "has_results": True,
            "stats": stats,
            "results": results
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==================== ФАЗА 3: DASHBOARD УЧЕНИКОВ ====================

@app.route('/api/students', methods=['GET'])
def get_students():
    """
    Получить список всех учеников с фильтрацией и сортировкой

    Query params:
        - search: поиск по имени или email
        - sort_by: поле для сортировки (name, last_activity, avg_score, quizzes_taken)
        - sort_order: направление сортировки (asc/desc)
        - limit: количество результатов (по умолчанию 100)
        - offset: смещение для пагинации
    """
    try:
        search = request.args.get('search', '').strip()
        sort_by = request.args.get('sort_by', 'last_activity')
        sort_order = request.args.get('sort_order', 'desc')
        limit = request.args.get('limit', default=100, type=int)
        offset = request.args.get('offset', default=0, type=int)

        with db.get_connection() as conn:
            cursor = conn.cursor()

            # Базовый запрос из представления student_stats
            query = "SELECT * FROM student_stats WHERE 1=1"
            params = []

            # Поиск по имени или email
            if search:
                query += " AND (student_name LIKE ? OR student_email LIKE ?)"
                search_pattern = f"%{search}%"
                params.extend([search_pattern, search_pattern])

            # Сортировка
            valid_sort_fields = ['student_name', 'last_activity', 'avg_score', 'quizzes_taken', 'total_attempts']
            if sort_by in valid_sort_fields:
                query += f" ORDER BY {sort_by}"
                if sort_order.lower() == 'desc':
                    query += " DESC"
                else:
                    query += " ASC"
            else:
                query += " ORDER BY last_activity DESC"

            # Пагинация
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            students = [dict(row) for row in cursor.fetchall()]

            # Получаем общее количество учеников (для пагинации)
            count_query = "SELECT COUNT(*) as total FROM student_stats WHERE 1=1"
            count_params = []
            if search:
                count_query += " AND (student_name LIKE ? OR student_email LIKE ?)"
                search_pattern = f"%{search}%"
                count_params.extend([search_pattern, search_pattern])

            cursor.execute(count_query, count_params)
            total = cursor.fetchone()['total']

            return jsonify({
                "success": True,
                "students": students,
                "total": total,
                "limit": limit,
                "offset": offset
            })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/students/<student_name>', methods=['GET'])
def get_student_profile(student_name):
    """
    Получить профиль ученика со статистикой
    """
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()

            # Получаем статистику ученика
            cursor.execute("""
                SELECT * FROM student_stats WHERE student_name = ?
            """, (student_name,))

            profile = cursor.fetchone()
            if not profile:
                return jsonify({
                    "success": False,
                    "error": "Ученик не найден"
                }), 404

            profile = dict(profile)

            # Получаем все попытки ученика с деталями
            cursor.execute("""
                SELECT * FROM attempt_details
                WHERE student_name = ?
                ORDER BY started_at DESC
            """, (student_name,))

            attempts = [dict(row) for row in cursor.fetchall()]
            profile['attempts'] = attempts

            return jsonify({
                "success": True,
                "profile": profile
            })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/students/<student_name>/attempts', methods=['GET'])
def get_student_attempts(student_name):
    """
    Получить все попытки ученика с фильтрацией

    Query params:
        - quiz_id: фильтр по викторине
        - completed_only: только завершенные (true/false)
        - limit: количество результатов
        - offset: смещение для пагинации
    """
    try:
        quiz_id = request.args.get('quiz_id', type=int)
        completed_only = request.args.get('completed_only', 'false').lower() == 'true'
        limit = request.args.get('limit', default=50, type=int)
        offset = request.args.get('offset', default=0, type=int)

        with db.get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM attempt_details WHERE student_name = ?"
            params = [student_name]

            if quiz_id:
                query += " AND quiz_id = ?"
                params.append(quiz_id)

            if completed_only:
                query += " AND completed_at IS NOT NULL"

            query += " ORDER BY started_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            attempts = [dict(row) for row in cursor.fetchall()]

            return jsonify({
                "success": True,
                "attempts": attempts,
                "student_name": student_name
            })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==================== ЗАМЕТКИ ПРЕПОДАВАТЕЛЯ ====================

@app.route('/api/attempts/<int:attempt_id>/notes', methods=['GET', 'POST'])
def manage_attempt_notes(attempt_id):
    """
    GET: Получить все заметки для попытки
    POST: Добавить новую заметку
    """
    if request.method == 'GET':
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM teacher_notes
                    WHERE attempt_id = ?
                    ORDER BY created_at DESC
                """, (attempt_id,))

                notes = [dict(row) for row in cursor.fetchall()]

                return jsonify({
                    "success": True,
                    "notes": notes
                })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    else:  # POST
        try:
            data = request.get_json()

            if not data or 'note_text' not in data:
                return jsonify({
                    "success": False,
                    "error": "Текст заметки обязателен"
                }), 400

            with db.get_connection() as conn:
                cursor = conn.cursor()

                # Проверяем существование попытки
                cursor.execute("SELECT id FROM quiz_attempts WHERE id = ?", (attempt_id,))
                if not cursor.fetchone():
                    return jsonify({
                        "success": False,
                        "error": "Попытка не найдена"
                    }), 404

                # Добавляем заметку
                cursor.execute("""
                    INSERT INTO teacher_notes (
                        attempt_id, teacher_name, note_text, note_type, is_private
                    )
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    attempt_id,
                    data.get('teacher_name'),
                    data['note_text'],
                    data.get('note_type', 'general'),
                    data.get('is_private', False)
                ))

                note_id = cursor.lastrowid

                # Получаем созданную заметку
                cursor.execute("SELECT * FROM teacher_notes WHERE id = ?", (note_id,))
                note = dict(cursor.fetchone())

                return jsonify({
                    "success": True,
                    "note": note
                }), 201

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


@app.route('/api/notes/<int:note_id>', methods=['PUT', 'DELETE'])
def manage_note(note_id):
    """
    PUT: Обновить заметку
    DELETE: Удалить заметку
    """
    if request.method == 'PUT':
        try:
            data = request.get_json()

            with db.get_connection() as conn:
                cursor = conn.cursor()

                # Проверяем существование заметки
                cursor.execute("SELECT id FROM teacher_notes WHERE id = ?", (note_id,))
                if not cursor.fetchone():
                    return jsonify({
                        "success": False,
                        "error": "Заметка не найдена"
                    }), 404

                # Обновляем заметку
                update_fields = []
                params = []

                if 'note_text' in data:
                    update_fields.append("note_text = ?")
                    params.append(data['note_text'])

                if 'note_type' in data:
                    update_fields.append("note_type = ?")
                    params.append(data['note_type'])

                if 'is_private' in data:
                    update_fields.append("is_private = ?")
                    params.append(data['is_private'])

                if update_fields:
                    update_fields.append("updated_at = CURRENT_TIMESTAMP")
                    query = f"UPDATE teacher_notes SET {', '.join(update_fields)} WHERE id = ?"
                    params.append(note_id)
                    cursor.execute(query, params)

                # Получаем обновленную заметку
                cursor.execute("SELECT * FROM teacher_notes WHERE id = ?", (note_id,))
                note = dict(cursor.fetchone())

                return jsonify({
                    "success": True,
                    "note": note
                })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    else:  # DELETE
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("DELETE FROM teacher_notes WHERE id = ?", (note_id,))

                if cursor.rowcount == 0:
                    return jsonify({
                        "success": False,
                        "error": "Заметка не найдена"
                    }), 404

                return jsonify({
                    "success": True,
                    "message": "Заметка удалена"
                })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


# ==================== ТЕГИ ПОПЫТОК ====================

@app.route('/api/attempts/<int:attempt_id>/tags', methods=['GET', 'POST'])
def manage_attempt_tags(attempt_id):
    """
    GET: Получить все теги для попытки
    POST: Добавить новый тег
    """
    if request.method == 'GET':
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM attempt_tags
                    WHERE attempt_id = ?
                    ORDER BY created_at DESC
                """, (attempt_id,))

                tags = [dict(row) for row in cursor.fetchall()]

                return jsonify({
                    "success": True,
                    "tags": tags
                })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    else:  # POST
        try:
            data = request.get_json()

            if not data or 'tag_name' not in data:
                return jsonify({
                    "success": False,
                    "error": "Название тега обязательно"
                }), 400

            with db.get_connection() as conn:
                cursor = conn.cursor()

                # Проверяем существование попытки
                cursor.execute("SELECT id FROM quiz_attempts WHERE id = ?", (attempt_id,))
                if not cursor.fetchone():
                    return jsonify({
                        "success": False,
                        "error": "Попытка не найдена"
                    }), 404

                # Добавляем тег
                cursor.execute("""
                    INSERT INTO attempt_tags (attempt_id, tag_name, tag_color, created_by)
                    VALUES (?, ?, ?, ?)
                """, (
                    attempt_id,
                    data['tag_name'],
                    data.get('tag_color', 'blue'),
                    data.get('created_by')
                ))

                tag_id = cursor.lastrowid

                # Получаем созданный тег
                cursor.execute("SELECT * FROM attempt_tags WHERE id = ?", (tag_id,))
                tag = dict(cursor.fetchone())

                return jsonify({
                    "success": True,
                    "tag": tag
                }), 201

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


@app.route('/api/attempt-tags/<int:tag_id>', methods=['DELETE'])
def delete_attempt_tag(tag_id):
    """Удалить тег попытки"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("DELETE FROM attempt_tags WHERE id = ?", (tag_id,))

            if cursor.rowcount == 0:
                return jsonify({
                    "success": False,
                    "error": "Тег не найден"
                }), 404

            return jsonify({
                "success": True,
                "message": "Тег удален"
            })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==================== СИСТЕМА ПЕРСОНАЛЬНЫХ ПРИГЛАШЕНИЙ ====================

@app.route('/api/quizzes/<int:quiz_id>/invitations', methods=['GET', 'POST'])
def manage_quiz_invitations(quiz_id):
    """
    GET: Получить все приглашения для викторины
    POST: Создать новое приглашение
    """
    if request.method == 'GET':
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()

                # Проверяем существование викторины
                cursor.execute("SELECT id FROM quizzes WHERE id = ?", (quiz_id,))
                if not cursor.fetchone():
                    return jsonify({
                        "success": False,
                        "error": "Викторина не найдена"
                    }), 404

                # Получаем все приглашения
                cursor.execute("""
                    SELECT * FROM invitation_details
                    WHERE quiz_id = ?
                    ORDER BY created_at DESC
                """, (quiz_id,))

                invitations = [dict(row) for row in cursor.fetchall()]

                return jsonify({
                    "success": True,
                    "invitations": invitations
                })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    else:  # POST
        try:
            data = request.get_json()

            if not data or 'student_name' not in data:
                return jsonify({
                    "success": False,
                    "error": "Имя студента обязательно"
                }), 400

            with db.get_connection() as conn:
                cursor = conn.cursor()

                # Проверяем существование викторины
                cursor.execute("SELECT id FROM quizzes WHERE id = ?", (quiz_id,))
                if not cursor.fetchone():
                    return jsonify({
                        "success": False,
                        "error": "Викторина не найдена"
                    }), 404

                # Генерируем уникальный токен
                import secrets
                unique_token = secrets.token_urlsafe(32)

                # Проверяем уникальность токена
                cursor.execute("SELECT id FROM quiz_invitations WHERE unique_token = ?", (unique_token,))
                while cursor.fetchone():
                    unique_token = secrets.token_urlsafe(32)
                    cursor.execute("SELECT id FROM quiz_invitations WHERE unique_token = ?", (unique_token,))

                # Создаем приглашение
                cursor.execute("""
                    INSERT INTO quiz_invitations (
                        quiz_id, student_name, student_email, unique_token,
                        expires_at, created_by, notes
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    quiz_id,
                    data['student_name'],
                    data.get('student_email'),
                    unique_token,
                    data.get('expires_at'),
                    data.get('created_by'),
                    data.get('notes')
                ))

                invitation_id = cursor.lastrowid

                # Получаем созданное приглашение
                cursor.execute("SELECT * FROM invitation_details WHERE id = ?", (invitation_id,))
                invitation = dict(cursor.fetchone())

                # Отправляем email если настроен и указан email студента
                invitation_link = f"{request.host_url}quiz.html?token={unique_token}"

                if email_service and data.get('student_email'):
                    # Получаем название викторины
                    cursor.execute("SELECT name FROM quizzes WHERE id = ?", (quiz_id,))
                    quiz_row = cursor.fetchone()
                    quiz_name = quiz_row['name'] if quiz_row else f"Викторина #{quiz_id}"

                    try:
                        email_service.send_quiz_invitation(
                            student_name=data['student_name'],
                            student_email=data['student_email'],
                            quiz_name=quiz_name,
                            invitation_link=invitation_link,
                            expires_at=data.get('expires_at'),
                            teacher_name=data.get('created_by'),
                            notes=data.get('notes')
                        )
                    except Exception as email_error:
                        print(f"⚠️  Ошибка отправки email: {email_error}")

                return jsonify({
                    "success": True,
                    "invitation": invitation,
                    "link": invitation_link
                }), 201

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


@app.route('/api/quizzes/invitations/<token>', methods=['GET'])
def get_invitation_by_token(token):
    """Получить информацию о приглашении по токену"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM invitation_details WHERE unique_token = ?
            """, (token,))

            invitation = cursor.fetchone()

            if not invitation:
                return jsonify({
                    "success": False,
                    "error": "Приглашение не найдено"
                }), 404

            invitation = dict(invitation)

            # Проверяем статус приглашения
            if invitation['status'] == 'Использовано':
                return jsonify({
                    "success": False,
                    "error": "Это приглашение уже использовано",
                    "invitation": invitation
                }), 403

            if invitation['status'] == 'Истекло':
                return jsonify({
                    "success": False,
                    "error": "Срок действия приглашения истек",
                    "invitation": invitation
                }), 403

            # Получаем викторину
            quiz = db.get_quiz(quiz_id=invitation['quiz_id'])

            if not quiz or not quiz.get('is_active'):
                return jsonify({
                    "success": False,
                    "error": "Викторина недоступна"
                }), 404

            return jsonify({
                "success": True,
                "invitation": invitation,
                "quiz": quiz
            })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/quizzes/invitations/<token>/start', methods=['POST'])
def start_quiz_by_invitation(token):
    """Начать викторину по приглашению"""
    try:
        data = request.get_json() or {}

        with db.get_connection() as conn:
            cursor = conn.cursor()

            # Получаем приглашение
            cursor.execute("""
                SELECT * FROM quiz_invitations WHERE unique_token = ?
            """, (token,))

            invitation = cursor.fetchone()

            if not invitation:
                return jsonify({
                    "success": False,
                    "error": "Приглашение не найдено"
                }), 404

            invitation = dict(invitation)

            # Проверяем, что приглашение не использовано
            if invitation['is_used']:
                return jsonify({
                    "success": False,
                    "error": "Это приглашение уже использовано"
                }), 403

            # Проверяем срок действия
            if invitation['expires_at']:
                from datetime import datetime
                expires_at = datetime.fromisoformat(invitation['expires_at'])
                if datetime.now() > expires_at:
                    return jsonify({
                        "success": False,
                        "error": "Срок действия приглашения истек"
                    }), 403

            # Создаем попытку прохождения
            attempt = db.start_quiz_attempt(
                quiz_id=invitation['quiz_id'],
                student_name=invitation['student_name'],
                student_email=invitation['student_email'],
                ip_address=data.get('ip_address') or request.remote_addr
            )

            if not attempt:
                return jsonify({
                    "success": False,
                    "error": "Не удалось начать викторину"
                }), 500

            # Обновляем приглашение
            cursor.execute("""
                UPDATE quiz_invitations
                SET is_used = 1, used_at = CURRENT_TIMESTAMP, attempt_id = ?
                WHERE id = ?
            """, (attempt['id'], invitation['id']))

            # Обновляем попытку
            cursor.execute("""
                UPDATE quiz_attempts
                SET invitation_id = ?
                WHERE id = ?
            """, (invitation['id'], attempt['id']))

            conn.commit()

            return jsonify({
                "success": True,
                "attempt": attempt,
                "message": "Викторина успешно начата"
            })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/invitations/<int:invitation_id>', methods=['DELETE'])
def delete_invitation(invitation_id):
    """Удалить приглашение (если оно не использовано)"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()

            # Проверяем, что приглашение не использовано
            cursor.execute("""
                SELECT is_used FROM quiz_invitations WHERE id = ?
            """, (invitation_id,))

            invitation = cursor.fetchone()

            if not invitation:
                return jsonify({
                    "success": False,
                    "error": "Приглашение не найдено"
                }), 404

            if invitation['is_used']:
                return jsonify({
                    "success": False,
                    "error": "Нельзя удалить использованное приглашение"
                }), 403

            cursor.execute("DELETE FROM quiz_invitations WHERE id = ?", (invitation_id,))

            return jsonify({
                "success": True,
                "message": "Приглашение удалено"
            })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==================== AI-АНАЛИЗ С GEMINI (ФАЗА 4) ====================

# Инициализируем Gemini сервис (если установлен API ключ)
try:
    from api.gemini_service import GeminiService
    gemini_service = GeminiService()
    print("✅ Gemini AI инициализирован")
except Exception as e:
    gemini_service = None
    print(f"⚠️  Gemini AI не инициализирован: {e}")

# Инициализируем Email сервис (если настроен SMTP)
try:
    from api.email_service import EmailService
    email_service = EmailService()
    print("✅ Email сервис инициализирован")
except Exception as e:
    email_service = None
    print(f"⚠️  Email сервис не инициализирован: {e}")


@app.route('/api/ai/analyze-essay', methods=['POST'])
def ai_analyze_essay():
    """
    Анализ эссе с помощью AI

    Body:
        - answer_id: ID ответа в quiz_answers
        - question_text: текст вопроса (опционально)
        - student_answer: ответ студента (опционально)
        - guidelines: рекомендации (опционально)
    """
    if not gemini_service:
        return jsonify({
            "success": False,
            "error": "AI-сервис не настроен. Установите GEMINI_API_KEY"
        }), 503

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "Отсутствуют данные запроса"
            }), 400

        # Если передан answer_id, получаем данные из БД
        if 'answer_id' in data:
            with db.get_connection() as conn:
                cursor = conn.cursor()

                # Получаем ответ и вопрос
                cursor.execute("""
                    SELECT qa.*, q.text as question_text, q.explanation as guidelines
                    FROM quiz_answers qa
                    JOIN questions q ON qa.question_id = q.id
                    WHERE qa.id = ?
                """, (data['answer_id'],))

                row = cursor.fetchone()
                if not row:
                    return jsonify({
                        "success": False,
                        "error": "Ответ не найден"
                    }), 404

                answer_data = dict(row)
                question_text = answer_data['question_text']
                student_answer = answer_data['answer']
                guidelines = answer_data['guidelines']
                answer_id = data['answer_id']

                # Получаем промпт из викторины
                cursor.execute("""
                    SELECT q.ai_essay_analysis_prompt
                    FROM quizzes q
                    JOIN quiz_attempts qa ON q.id = qa.quiz_id
                    JOIN quiz_answers qans ON qa.id = qans.attempt_id
                    WHERE qans.id = ?
                """, (answer_id,))

                quiz_row = cursor.fetchone()
                prompt_template = quiz_row['ai_essay_analysis_prompt'] if quiz_row else None

        else:
            # Используем данные из запроса
            question_text = data.get('question_text')
            student_answer = data.get('student_answer')
            guidelines = data.get('guidelines')
            prompt_template = data.get('prompt_template')
            answer_id = None

            if not question_text or not student_answer:
                return jsonify({
                    "success": False,
                    "error": "Требуются question_text и student_answer"
                }), 400

        # Анализируем эссе
        result = gemini_service.analyze_essay(
            question_text=question_text,
            student_answer=student_answer,
            guidelines=guidelines,
            prompt_template=prompt_template
        )

        if not result['success']:
            return jsonify({
                "success": False,
                "error": f"Ошибка AI-анализа: {result.get('error')}"
            }), 500

        # Сохраняем результат в БД, если был answer_id
        if answer_id:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE quiz_answers
                    SET ai_essay_feedback = ?
                    WHERE id = ?
                """, (result['feedback'], answer_id))

        return jsonify({
            "success": True,
            "feedback": result['feedback'],
            "metadata": {
                'prompt_tokens': result.get('prompt_tokens'),
                'completion_tokens': result.get('completion_tokens')
            }
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/ai/analyze-quiz', methods=['POST'])
def ai_analyze_quiz():
    """
    Общий анализ прохождения викторины

    Body:
        - attempt_id: ID попытки прохождения
    """
    if not gemini_service:
        return jsonify({
            "success": False,
            "error": "AI-сервис не настроен. Установите GEMINI_API_KEY"
        }), 503

    try:
        data = request.get_json()

        if not data or 'attempt_id' not in data:
            return jsonify({
                "success": False,
                "error": "Требуется attempt_id"
            }), 400

        attempt_id = data['attempt_id']

        with db.get_connection() as conn:
            cursor = conn.cursor()

            # Получаем детали попытки
            cursor.execute("""
                SELECT qa.*, q.title as quiz_name, q.ai_quiz_analysis_prompt
                FROM quiz_attempts qa
                JOIN quizzes q ON qa.quiz_id = q.id
                WHERE qa.id = ?
            """, (attempt_id,))

            attempt = cursor.fetchone()
            if not attempt:
                return jsonify({
                    "success": False,
                    "error": "Попытка не найдена"
                }), 404

            attempt = dict(attempt)

            # Получаем все ответы с вопросами
            cursor.execute("""
                SELECT
                    qans.*,
                    q.text as question_text,
                    q.points as points_total
                FROM quiz_answers qans
                JOIN questions q ON qans.question_id = q.id
                WHERE qans.attempt_id = ?
            """, (attempt_id,))

            answers = [dict(row) for row in cursor.fetchall()]

            # Форматируем данные для анализа
            questions_data = []
            for ans in answers:
                questions_data.append({
                    'question_text': ans['question_text'],
                    'is_correct': ans['is_correct'],
                    'points_earned': ans['points_earned'],
                    'points_total': ans['points_total']
                })

            # Анализируем викторину
            result = gemini_service.analyze_quiz(
                quiz_name=attempt['quiz_name'],
                total_score=attempt['points_earned'] or 0,
                max_score=attempt['points_total'] or 0,
                questions_data=questions_data,
                prompt_template=attempt['ai_quiz_analysis_prompt']
            )

            if not result['success']:
                return jsonify({
                    "success": False,
                    "error": f"Ошибка AI-анализа: {result.get('error')}"
                }), 500

            # Сохраняем результат
            cursor.execute("""
                UPDATE quiz_attempts
                SET ai_quiz_overall_feedback = ?
                WHERE id = ?
            """, (result['feedback'], attempt_id))

            conn.commit()

            return jsonify({
                "success": True,
                "feedback": result['feedback'],
                "metadata": {
                    'prompt_tokens': result.get('prompt_tokens'),
                    'completion_tokens': result.get('completion_tokens')
                }
            })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/quizzes/<int:quiz_id>/ai-prompts', methods=['GET', 'PUT'])
def manage_ai_prompts(quiz_id):
    """
    GET: Получить AI-промпты викторины
    PUT: Обновить AI-промпты викторины
    """
    if request.method == 'GET':
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT ai_essay_analysis_prompt, ai_quiz_analysis_prompt
                    FROM quizzes
                    WHERE id = ?
                """, (quiz_id,))

                row = cursor.fetchone()
                if not row:
                    return jsonify({
                        "success": False,
                        "error": "Викторина не найдена"
                    }), 404

                return jsonify({
                    "success": True,
                    "prompts": dict(row)
                })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    else:  # PUT
        try:
            data = request.get_json()

            if not data:
                return jsonify({
                    "success": False,
                    "error": "Отсутствуют данные"
                }), 400

            with db.get_connection() as conn:
                cursor = conn.cursor()

                # Проверяем существование викторины
                cursor.execute("SELECT id FROM quizzes WHERE id = ?", (quiz_id,))
                if not cursor.fetchone():
                    return jsonify({
                        "success": False,
                        "error": "Викторина не найдена"
                    }), 404

                # Обновляем промпты
                update_fields = []
                params = []

                if 'ai_essay_analysis_prompt' in data:
                    update_fields.append("ai_essay_analysis_prompt = ?")
                    params.append(data['ai_essay_analysis_prompt'])

                if 'ai_quiz_analysis_prompt' in data:
                    update_fields.append("ai_quiz_analysis_prompt = ?")
                    params.append(data['ai_quiz_analysis_prompt'])

                if update_fields:
                    query = f"UPDATE quizzes SET {', '.join(update_fields)} WHERE id = ?"
                    params.append(quiz_id)
                    cursor.execute(query, params)

                # Получаем обновленные промпты
                cursor.execute("""
                    SELECT ai_essay_analysis_prompt, ai_quiz_analysis_prompt
                    FROM quizzes
                    WHERE id = ?
                """, (quiz_id,))

                return jsonify({
                    "success": True,
                    "prompts": dict(cursor.fetchone())
                })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


# ==================== КАСТОМНЫЕ URL И КОНТРОЛЬ ДОСТУПА ====================

@app.route('/api/quizzes/slug/<slug>', methods=['GET'])
def get_quiz_by_slug(slug):
    """Получить викторину по кастомному slug"""
    try:
        quiz = db.get_quiz_by_slug(slug)

        if not quiz:
            return jsonify({
                "success": False,
                "error": "Викторина не найдена"
            }), 404

        # Скрываем правильные ответы для студентов
        if not quiz.get('show_correct_answers'):
            for question in quiz.get('questions', []):
                for option in question.get('options', []):
                    option['is_correct'] = None

        return jsonify({
            "success": True,
            "quiz": quiz
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/quizzes/<int:quiz_id>/custom-slug', methods=['PUT'])
def set_custom_slug(quiz_id):
    """Установить кастомный URL для викторины"""
    try:
        data = request.get_json()

        if not data or 'custom_slug' not in data:
            return jsonify({
                "success": False,
                "error": "Необходимо указать custom_slug"
            }), 400

        success = db.set_custom_slug(quiz_id, data['custom_slug'])

        if not success:
            return jsonify({
                "success": False,
                "error": "Не удалось установить slug. Возможно, он уже занят или содержит недопустимые символы"
            }), 400

        return jsonify({
            "success": True,
            "message": "Custom slug установлен"
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/quizzes/<int:quiz_id>/access-control', methods=['GET', 'POST'])
def manage_access_control(quiz_id):
    """
    GET: Получить белый список доступа
    POST: Добавить запись в белый список
    """
    if request.method == 'GET':
        try:
            access_list = db.get_access_control_list(quiz_id)

            return jsonify({
                "success": True,
                "access_list": access_list
            })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    else:  # POST
        try:
            data = request.get_json()

            if not data or 'entry_type' not in data or 'entry_value' not in data:
                return jsonify({
                    "success": False,
                    "error": "Необходимо указать entry_type и entry_value"
                }), 400

            if data['entry_type'] not in ['email', 'domain']:
                return jsonify({
                    "success": False,
                    "error": "entry_type должен быть 'email' или 'domain'"
                }), 400

            success = db.add_access_control_entry(
                quiz_id=quiz_id,
                entry_type=data['entry_type'],
                entry_value=data['entry_value'],
                created_by=data.get('created_by'),
                notes=data.get('notes')
            )

            if not success:
                return jsonify({
                    "success": False,
                    "error": "Не удалось добавить запись. Возможно, она уже существует"
                }), 400

            # Возвращаем обновленный список
            access_list = db.get_access_control_list(quiz_id)

            return jsonify({
                "success": True,
                "message": "Запись добавлена в белый список",
                "access_list": access_list
            }), 201

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


@app.route('/api/quizzes/<int:quiz_id>/access-control/<int:entry_id>', methods=['DELETE'])
def delete_access_control_entry(quiz_id, entry_id):
    """Удалить запись из белого списка"""
    try:
        success = db.remove_access_control_entry(entry_id)

        if not success:
            return jsonify({
                "success": False,
                "error": "Запись не найдена"
            }), 404

        return jsonify({
            "success": True,
            "message": "Запись удалена из белого списка"
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/quizzes/<int:quiz_id>/check-access', methods=['POST'])
def check_quiz_access(quiz_id):
    """Проверить доступ к викторине по email"""
    try:
        data = request.get_json()

        if not data or 'email' not in data:
            return jsonify({
                "success": False,
                "error": "Необходимо указать email"
            }), 400

        has_access = db.check_email_access(quiz_id, data['email'])

        return jsonify({
            "success": True,
            "has_access": has_access
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/quizzes/<slug>/start-by-slug', methods=['POST'])
def start_quiz_by_slug(slug):
    """Начать прохождение викторины по slug"""
    try:
        data = request.get_json()

        if not data or not data.get('student_name'):
            return jsonify({
                "success": False,
                "error": "Необходимо указать student_name"
            }), 400

        # Получаем викторину по slug
        quiz = db.get_quiz_by_slug(slug)

        if not quiz:
            return jsonify({
                "success": False,
                "error": "Викторина не найдена"
            }), 404

        # Проверяем доступ по email, если требуется
        if quiz.get('require_email_validation'):
            if not data.get('student_email'):
                return jsonify({
                    "success": False,
                    "error": "Для этой викторины необходимо указать email"
                }), 400

            has_access = db.check_email_access(quiz['id'], data['student_email'])

            if not has_access:
                return jsonify({
                    "success": False,
                    "error": "Доступ к викторине запрещен. Ваш email не в белом списке."
                }), 403

        # Создаем попытку
        attempt = db.start_quiz_attempt(
            quiz_id=quiz['id'],
            student_name=data['student_name'],
            student_email=data.get('student_email'),
            ip_address=request.remote_addr
        )

        if not attempt:
            return jsonify({
                "success": False,
                "error": "Не удалось начать викторину"
            }), 400

        return jsonify({
            "success": True,
            "attempt": attempt,
            "session_id": attempt['unique_session_id']
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == '__main__':
    print("🚀 Запуск API сервера...")
    print("📍 API доступен по адресу: http://localhost:5001")
    print("📖 Эндпоинты:")
    print("   GET  /api/health              - Проверка работоспособности")
    print("   GET  /api/questions           - Список вопросов с фильтрацией")
    print("   GET  /api/questions/<id>      - Конкретный вопрос")
    print("   GET  /api/filters             - Доступные фильтры")
    print("   GET  /api/stats               - Статистика")
    print("   GET  /api/pdf/<path>          - Исходный PDF файл")
    print("   GET  /api/random              - Случайные вопросы")
    print("   POST /api/check_answer        - Проверить ответ")
    print("\n   === УПРАВЛЕНИЕ PDF ===")
    print("   GET  /api/pdfs                - Список PDF с фильтрацией")
    print("   POST /api/pdfs                - Создать ручной PDF")
    print("   GET  /api/pdfs/<id>           - Информация о PDF")
    print("   PUT  /api/pdfs/<id>           - Обновить метаданные PDF")
    print("   POST /api/pdfs/upload         - Загрузить PDF файл")
    print("   POST /api/pdfs/<id>/reparse   - Перепарсить PDF (превью)")
    print("   POST /api/pdfs/<id>/apply-reparse - Применить перепарсинг")
    print("   GET  /api/pdfs/<id>/verification-stats - Статистика проверки")
    print("   PUT  /api/pdfs/<id>/verification-status - Обновить статус проверки")
    print("\n   === ПРОВЕРКА ВОПРОСОВ ===")
    print("   PUT  /api/questions/<id>/verify - Пометить вопрос как проверенный")
    print("   POST /api/questions/bulk-verify - Массовая проверка вопросов")
    print("\n   === АДМИНИСТРИРОВАНИЕ ===")
    print("   POST /api/admin/backup        - Создать бэкап БД")
    print("   POST /api/admin/sync-db       - Синхронизировать БД")
    print("\n   === ЗАГРУЗЧИК ИЗ СЕТИ ===")
    print("   GET  /api/downloader/sources  - Список источников загрузки")
    print("   POST /api/downloader/sources  - Добавить источник")
    print("   PUT  /api/downloader/sources/<name> - Обновить источник")
    print("   DEL  /api/downloader/sources/<name> - Удалить источник")
    print("   GET  /api/downloader/subjects - Список предметов для поиска")
    print("   POST /api/downloader/subjects - Добавить предмет")
    print("   DEL  /api/downloader/subjects/<name> - Удалить предмет")
    print("   POST /api/downloader/start    - Запустить загрузчик")
    print("   GET  /api/downloader/logs     - Получить логи")
    print("   GET  /api/downloader/stats    - Статистика загрузок")
    print("\n   === ВИКТОРИНЫ ===")
    print("   GET  /api/source-pdfs         - Список PDF файлов")
    print("   GET  /api/questions/by-pdf    - Вопросы из PDF")
    print("   GET/POST /api/quizzes         - Список/создание викторин")
    print("   GET/PUT/DEL /api/quizzes/<id> - Управление викториной")
    print("   GET  /api/quizzes/code/<code> - Викторина по коду")
    print("   POST /api/quizzes/<code>/start - Начать викторину")
    print("   POST /api/quizzes/session/<id>/answer - Отправить ответ")
    print("   POST /api/quizzes/session/<id>/complete - Завершить")
    print("   GET  /api/quizzes/<id>/attempts - Попытки викторины")
    print("   GET  /api/quizzes/session/<id> - Детали попытки")
    print("\n   === DASHBOARD УЧЕНИКОВ (ФАЗА 3) ===")
    print("   GET  /api/students            - Список учеников с фильтрацией")
    print("   GET  /api/students/<name>     - Профиль ученика")
    print("   GET  /api/students/<name>/attempts - Попытки ученика")
    print("   GET/POST /api/attempts/<id>/notes - Заметки преподавателя")
    print("   PUT/DEL /api/notes/<id>       - Управление заметкой")
    print("   GET/POST /api/attempts/<id>/tags - Теги попытки")
    print("   DEL  /api/attempt-tags/<id>   - Удалить тег")
    print("\n   === ПЕРСОНАЛЬНЫЕ ПРИГЛАШЕНИЯ ===")
    print("   GET/POST /api/quizzes/<id>/invitations - Приглашения викторины")
    print("   GET  /api/quizzes/invitations/<token> - Информация о приглашении")
    print("   POST /api/quizzes/invitations/<token>/start - Начать по приглашению")
    print("   DEL  /api/invitations/<id>    - Удалить приглашение")
    print("\n   === AI-АНАЛИЗ (GEMINI) ===")
    print("   POST /api/ai/analyze-essay    - Анализ эссе с AI")
    print("   POST /api/ai/analyze-quiz     - Общий анализ викторины")
    print("   GET/PUT /api/quizzes/<id>/ai-prompts - Управление AI-промптами")
    print("\n   === ИЗОБРАЖЕНИЯ ===")
    print("   POST /api/images/upload       - Загрузить изображение")
    print("   GET  /api/images/<path>       - Получить изображение")
    print("   DEL  /api/images/<id>         - Удалить изображение")
    print("   GET  /api/questions/<id>/images - Изображения вопроса")
    print("   GET  /api/options/<id>/images - Изображения варианта ответа")
    print()

    app.run(debug=True, host='0.0.0.0', port=5001)
