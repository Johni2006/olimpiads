// Функции для работы с викторинами

let allQuizzes = []; // Все созданные викторины

// ==================== ЗАГРУЗКА ДАННЫХ ====================

// Загрузить список викторин
async function loadQuizzes() {
    try {
        const response = await fetch(`${API_URL}/quizzes`);
        const data = await response.json();

        if (data.success) {
            allQuizzes = data.quizzes;
            displayQuizzes(allQuizzes);
        }
    } catch (error) {
        console.error('Ошибка загрузки викторин:', error);
    }
}

// ==================== ОТОБРАЖЕНИЕ ====================

// Отобразить список викторин
function displayQuizzes(quizzes) {
    const container = document.getElementById('quizzes-container');

    if (quizzes.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <p style="color: #999;">Вы еще не создали ни одной викторины</p>
            </div>
        `;
        return;
    }

    container.innerHTML = quizzes.map(quiz => {
        const isDraft = quiz.status === 'draft';
        const statusColor = isDraft ? '#4caf50' : '#9e9e9e';
        const statusText = isDraft ? '🟢 Черновик' : '🔴 Готова';
        const statusButtonText = isDraft ? '✅ Завершить' : '📝 В черновик';

        return `
        <div class="question-card" style="margin-bottom: 15px; border-left: 4px solid ${statusColor};">
            <div class="question-header">
                <div>
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 5px;">
                        <h3 style="margin: 0;">${quiz.title}</h3>
                        <span style="padding: 4px 12px; background: ${statusColor}; color: white; border-radius: 12px; font-size: 0.85em; font-weight: 600;">
                            ${statusText}
                        </span>
                    </div>
                    <p style="color: #666; margin-bottom: 10px;">${quiz.description || ''}</p>
                    <div class="question-meta">
                        <span class="tag">Вопросов: ${quiz.question_count || 0}</span>
                        <span class="tag">Попыток: ${quiz.total_attempts || 0}</span>
                        <span class="tag">Завершено: ${quiz.completed_attempts || 0}</span>
                        ${quiz.avg_score ? `<span class="tag">Средний балл: ${quiz.avg_score.toFixed(1)}%</span>` : ''}
                    </div>
                </div>
                <div style="display: flex; flex-direction: column; gap: 10px; align-items: flex-end;">
                    <div style="font-size: 1.2em; font-weight: bold; color: #667eea;">
                        Код: ${quiz.unique_code}
                    </div>
                    <div style="display: flex; gap: 10px; flex-wrap: wrap; justify-content: flex-end;">
                        <button onclick="toggleQuizStatus(${quiz.id}, '${isDraft ? 'ready' : 'draft'}')" class="btn-secondary" style="padding: 8px 15px; background: ${statusColor};">
                            ${statusButtonText}
                        </button>
                        <button onclick="viewQuizQuestions(${quiz.id}, '${quiz.title.replace(/'/g, "\\'")}')" class="btn-secondary" style="padding: 8px 15px;">
                            📝 Вопросы
                        </button>
                        <button onclick="copyQuizLink('${quiz.unique_code}')" class="btn-secondary" style="padding: 8px 15px;">
                            📋 Ссылка
                        </button>
                        <button onclick="viewQuizResults(${quiz.id})" class="btn-secondary" style="padding: 8px 15px;">
                            📊 Результаты
                        </button>
                        <button onclick="deleteQuiz(${quiz.id})" class="btn-secondary" style="padding: 8px 15px; background: #f44336;">
                            🗑️ Удалить
                        </button>
                    </div>
                </div>
            </div>
        </div>
        `;
    }).join('');
}

// ==================== СОЗДАНИЕ ВИКТОРИНЫ ====================

// Функции для ручного выбора вопросов (showPdfSelector, showManualSelector, loadQuestionsFromPdf)
// были удалены, так как не используются в текущем интерфейсе.
// Вместо этого используется функция addQuestionToQuiz() из app.js,
// которая показывает список существующих викторин и добавляет вопросы туда.

// Создать викторину
async function createQuiz() {
    const title = document.getElementById('quiz-title').value.trim();
    const description = document.getElementById('quiz-description').value.trim();
    const creator = document.getElementById('quiz-creator').value.trim();
    const maxAttempts = parseInt(document.getElementById('quiz-max-attempts').value);

    // Валидация
    if (!title) {
        alert('❌ Введите название викторины');
        return;
    }

    // Создаем викторину через API (без вопросов - их добавим потом)
    try {
        const response = await fetch(`${API_URL}/quizzes`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                title: title,
                description: description,
                created_by: creator || 'Учитель',
                max_attempts: maxAttempts,
                show_correct_answers: false,
                allow_review: true,
                pass_threshold: 0.0,
                shuffle_questions: false,
                shuffle_options: false,
                status: 'draft'
            })
        });

        const data = await response.json();

        if (data.success) {
            alert(`✅ Викторина создана!\n\nТеперь перейдите на вкладку "Просмотр вопросов" и добавьте вопросы в викторину.`);

            // Очищаем форму
            document.getElementById('quiz-title').value = '';
            document.getElementById('quiz-description').value = '';

            // Перезагружаем список викторин
            loadQuizzes();

            // Обновляем выпадающий список викторин на вкладке вопросов
            if (typeof loadDraftQuizzesForSelector === 'function') {
                loadDraftQuizzesForSelector();
            }
        } else {
            alert(`❌ Ошибка создания викторины: ${data.error}`);
        }
    } catch (error) {
        console.error('Ошибка создания викторины:', error);
        alert('❌ Ошибка создания викторины');
    }
}

// ==================== ДЕЙСТВИЯ С ВИКТОРИНАМИ ====================

// Копировать ссылку на викторину
function copyQuizLink(code) {
    const link = `${window.location.origin}/quiz.html?code=${code}`;

    // Копируем в буфер обмена
    navigator.clipboard.writeText(link).then(() => {
        alert(`✅ Ссылка скопирована!\n\n${link}\n\nОтправьте эту ссылку ученикам для прохождения викторины.`);
    }).catch(err => {
        alert(`Ссылка на викторину:\n\n${link}\n\nСкопируйте её вручную.`);
    });
}

// Просмотреть результаты викторины
async function viewQuizResults(quizId) {
    try {
        const response = await fetch(`${API_URL}/quizzes/${quizId}/attempts?completed_only=true`);
        const data = await response.json();

        if (data.success) {
            displayQuizResultsModal(data.attempts);
        }
    } catch (error) {
        console.error('Ошибка загрузки результатов:', error);
        alert('❌ Ошибка загрузки результатов');
    }
}

// Отобразить модальное окно с результатами
function displayQuizResultsModal(attempts) {
    const modal = document.getElementById('edit-modal');

    if (attempts.length === 0) {
        alert('Ещё никто не прошел эту викторину');
        return;
    }

    // Сортируем по баллам (убывание)
    attempts.sort((a, b) => b.score - a.score);

    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2>📊 Результаты викторины</h2>
                <button class="close-btn" onclick="closeEditModal()">✕</button>
            </div>
            <div class="modal-body">
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background: #f5f5f5;">
                            <th style="padding: 10px; text-align: left;">Место</th>
                            <th style="padding: 10px; text-align: left;">Ученик</th>
                            <th style="padding: 10px; text-align: center;">Балл</th>
                            <th style="padding: 10px; text-align: center;">Правильных</th>
                            <th style="padding: 10px; text-align: center;">Время</th>
                            <th style="padding: 10px; text-align: center;">Дата</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${attempts.map((attempt, index) => `
                            <tr style="border-bottom: 1px solid #e0e0e0;">
                                <td style="padding: 10px;">${index + 1}</td>
                                <td style="padding: 10px;">${attempt.student_name}</td>
                                <td style="padding: 10px; text-align: center; font-weight: bold; color: ${attempt.score >= 70 ? '#4caf50' : attempt.score >= 50 ? '#ff9800' : '#f44336'};">
                                    ${attempt.score.toFixed(1)}%
                                </td>
                                <td style="padding: 10px; text-align: center;">
                                    ${attempt.correct_answers} / ${attempt.total_questions}
                                </td>
                                <td style="padding: 10px; text-align: center;">
                                    ${attempt.time_spent ? Math.floor(attempt.time_spent / 60) + ' мин' : '-'}
                                </td>
                                <td style="padding: 10px; text-align: center;">
                                    ${new Date(attempt.completed_at).toLocaleString('ru-RU')}
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>

                <div style="margin-top: 20px; padding: 15px; background: #f5f5f5; border-radius: 8px;">
                    <h4>Статистика:</h4>
                    <p><strong>Средний балл:</strong> ${(attempts.reduce((sum, a) => sum + a.score, 0) / attempts.length).toFixed(1)}%</p>
                    <p><strong>Прошедших:</strong> ${attempts.filter(a => a.is_passed).length} из ${attempts.length}</p>
                </div>
            </div>
        </div>
    `;

    modal.style.display = 'flex';
}

// Переключить статус викторины
async function toggleQuizStatus(quizId, newStatus) {
    const statusText = newStatus === 'ready' ? 'завершенной' : 'черновиком';
    const confirmMessage = newStatus === 'ready'
        ? 'Вы уверены, что хотите завершить викторину?\n\nПосле этого вы не сможете добавлять или удалять вопросы.'
        : 'Вернуть викторину в статус черновика?\n\nВы снова сможете редактировать вопросы.';

    if (!confirm(confirmMessage)) {
        return;
    }

    try {
        const response = await fetch(`${API_URL}/quizzes/${quizId}/status`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                status: newStatus
            })
        });

        const data = await response.json();

        if (data.success) {
            alert(`✅ Викторина теперь является ${statusText}`);
            loadQuizzes();
        } else {
            alert(`❌ Ошибка: ${data.error}`);
        }
    } catch (error) {
        console.error('Ошибка изменения статуса викторины:', error);
        alert('❌ Ошибка изменения статуса викторины');
    }
}

// Удалить викторину
async function deleteQuiz(quizId) {
    if (!confirm('Вы уверены, что хотите удалить эту викторину? Это действие нельзя отменить.')) {
        return;
    }

    try {
        const response = await fetch(`${API_URL}/quizzes/${quizId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            alert('✅ Викторина удалена');
            loadQuizzes();
        } else {
            alert(`❌ Ошибка: ${data.error}`);
        }
    } catch (error) {
        console.error('Ошибка удаления викторины:', error);
        alert('❌ Ошибка удаления викторины');
    }
}

// Просмотр вопросов викторины
async function viewQuizQuestions(quizId, quizTitle) {
    try {
        const response = await fetch(`${API_URL}/quizzes/${quizId}/questions`);
        const data = await response.json();

        if (!data.success) {
            alert(`❌ Ошибка: ${data.error}`);
            return;
        }

        const questions = data.questions || [];

        // Создаем модальное окно
        const modal = document.getElementById('edit-modal');
        if (!modal) return;

        modal.innerHTML = `
            <div class="modal-content" style="max-width: 900px;">
                <div class="modal-header">
                    <h2>📝 Вопросы викторины: ${quizTitle}</h2>
                    <button class="close-btn" onclick="closeEditModal()">✕</button>
                </div>
                <div class="modal-body">
                    ${questions.length === 0 ? `
                        <div style="text-align: center; padding: 40px; color: #999;">
                            <p style="font-size: 18px;">В этой викторине пока нет вопросов</p>
                            <p style="margin-top: 10px;">Перейдите на вкладку "Просмотр вопросов" и добавьте вопросы в викторину</p>
                        </div>
                    ` : `
                        <div style="margin-bottom: 20px; padding: 15px; background: #f0f8ff; border-radius: 8px;">
                            <p style="margin: 0; color: #555;">
                                Всего вопросов в викторине: <strong>${questions.length}</strong>
                            </p>
                        </div>
                        <div style="display: flex; flex-direction: column; gap: 15px;">
                            ${questions.map((q, index) => {
                                const typeIcon = {
                                    'choice': '🔘',
                                    'multiple_choice': '☑️',
                                    'text': '📝',
                                    'essay': '📄',
                                    'matching': '🔗'
                                }[q.type] || '❓';

                                const typeText = {
                                    'choice': 'Одиночный выбор',
                                    'multiple_choice': 'Множественный выбор',
                                    'text': 'Текстовый ответ',
                                    'essay': 'Эссе',
                                    'matching': 'Соответствие'
                                }[q.type] || q.type;

                                let answersHTML = '';
                                if (q.type === 'choice' || q.type === 'multiple_choice') {
                                    answersHTML = `
                                        <div style="margin-top: 10px;">
                                            <strong>Варианты ответов:</strong>
                                            <ul style="margin-top: 5px; padding-left: 20px;">
                                                ${(q.options || []).map(opt => `
                                                    <li style="color: ${opt.is_correct ? '#4caf50' : '#666'};">
                                                        ${opt.text} ${opt.is_correct ? '✓ (правильный)' : ''}
                                                    </li>
                                                `).join('')}
                                            </ul>
                                        </div>
                                    `;
                                } else if (q.type === 'text') {
                                    answersHTML = `
                                        <div style="margin-top: 10px;">
                                            <strong>Правильный ответ:</strong> ${q.correct_text || '-'}
                                        </div>
                                    `;
                                } else if (q.type === 'matching') {
                                    answersHTML = `
                                        <div style="margin-top: 10px;">
                                            <strong>Пары для сопоставления:</strong>
                                            <ul style="margin-top: 5px; padding-left: 20px;">
                                                ${(q.matching_pairs || []).map(pair => `
                                                    <li>${pair.left_text} → ${pair.right_text}</li>
                                                `).join('')}
                                            </ul>
                                        </div>
                                    `;
                                }

                                const tagsHTML = (q.tags && q.tags.length > 0) ? `
                                    <div style="margin-top: 10px;">
                                        ${q.tags.map(tag => `
                                            <span style="display: inline-block; padding: 4px 10px; background: #e3f2fd; color: #1976d2; border-radius: 12px; font-size: 12px; margin-right: 5px;">
                                                ${tag}
                                            </span>
                                        `).join('')}
                                    </div>
                                ` : '';

                                return `
                                    <div style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 15px; background: white;">
                                        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
                                            <div style="flex: 1;">
                                                <div style="font-size: 14px; color: #999; margin-bottom: 5px;">
                                                    Вопрос ${index + 1} • ${typeIcon} ${typeText} • ${q.points || 1} баллов
                                                </div>
                                                <div style="font-size: 16px; font-weight: 500; color: #333;">
                                                    ${q.text}
                                                </div>
                                            </div>
                                        </div>
                                        ${answersHTML}
                                        ${tagsHTML}
                                    </div>
                                `;
                            }).join('')}
                        </div>
                    `}
                </div>
            </div>
        `;

        modal.style.display = 'flex';
    } catch (error) {
        console.error('Ошибка загрузки вопросов:', error);
        alert('❌ Ошибка загрузки вопросов викторины');
    }
}

// ==================== ИНИЦИАЛИЗАЦИЯ ====================

// Загрузить викторины при переключении на таб
window.addEventListener('DOMContentLoaded', () => {
    // Загружаем викторины при инициализации
    loadQuizzes();
});
