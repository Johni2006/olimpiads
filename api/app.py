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
import json
import os
import subprocess
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Разрешаем CORS для работы с фронтендом

# Инициализируем БД
db = DatabaseManager("olympiad_questions.db")


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
        limit = request.args.get('limit', default=50, type=int)
        offset = request.args.get('offset', default=0, type=int)

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
                "topic": topic
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
        return jsonify({
            "success": False,
            "error": str(e)
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
        # 1. Удаляем теги
        cursor.execute("DELETE FROM tags WHERE question_id = ?", (question_id,))

        # 2. Удаляем варианты ответов
        cursor.execute("DELETE FROM options WHERE question_id = ?", (question_id,))

        # 3. Удаляем пары для matching
        cursor.execute("DELETE FROM matching_pairs WHERE question_id = ?", (question_id,))

        # 4. Удаляем сам вопрос
        cursor.execute("DELETE FROM questions WHERE id = ?", (question_id,))

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
        question_id = db.add_question(data)

        if question_id:
            return jsonify({
                "success": True,
                "message": "Вопрос создан",
                "question_id": question_id
            })
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
            limit = request.args.get('limit', default=100, type=int)
            offset = request.args.get('offset', default=0, type=int)

            if is_active is not None:
                is_active = is_active.lower() == 'true'

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
            # 1. Удаляем теги вопросов
            cursor.execute("""
                DELETE FROM tags WHERE question_id IN (
                    SELECT id FROM questions WHERE source_pdf = ?
                )
            """, (file_path,))

            # 2. Удаляем варианты ответов
            cursor.execute("""
                DELETE FROM options WHERE question_id IN (
                    SELECT id FROM questions WHERE source_pdf = ?
                )
            """, (file_path,))

            # 3. Удаляем пары для matching
            cursor.execute("""
                DELETE FROM matching_pairs WHERE question_id IN (
                    SELECT id FROM questions WHERE source_pdf = ?
                )
            """, (file_path,))

            # 4. Удаляем вопросы
            cursor.execute("DELETE FROM questions WHERE source_pdf = ?", (file_path,))

            # 5. Удаляем запись о PDF
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
        image_type = request.form.get('image_type', 'other')
        description = request.form.get('description', '')

        # Определяем директорию для сохранения
        if option_id:
            upload_dir = Path(__file__).parent.parent / 'uploads' / 'option_images'
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
        else:
            relative_path = f"uploads/question_images/{unique_filename}"

        # Сохраняем в БД
        conn = db.conn
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO images (
                question_id, option_id, file_path, image_type,
                width, height, description
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (question_id, option_id, relative_path, image_type, width, height, description))

        image_id = cursor.lastrowid
        conn.commit()

        return jsonify({
            "success": True,
            "image_id": image_id,
            "file_path": relative_path,
            "width": width,
            "height": height,
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
    print("\n   === ИЗОБРАЖЕНИЯ ===")
    print("   POST /api/images/upload       - Загрузить изображение")
    print("   GET  /api/images/<path>       - Получить изображение")
    print("   DEL  /api/images/<id>         - Удалить изображение")
    print("   GET  /api/questions/<id>/images - Изображения вопроса")
    print("   GET  /api/options/<id>/images - Изображения варианта ответа")
    print()

    app.run(debug=True, host='0.0.0.0', port=5001)
