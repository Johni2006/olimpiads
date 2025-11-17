// Функции для работы с викторинами

let selectedQuestions = []; // Вопросы выбранные вручную
let pdfQuestions = []; // Вопросы из выбранного PDF
let allQuizzes = []; // Все созданные викторины

// ==================== ЗАГРУЗКА ДАННЫХ ====================

// Загрузить список PDF файлов
async function loadPDFListForQuiz() {
    try {
        const response = await fetch(`${API_URL}/source-pdfs`);
        const data = await response.json();

        if (data.success) {
            const select = document.getElementById('pdf-select');
            select.innerHTML = '<option value="">-- Выберите PDF --</option>';

            data.pdfs.forEach(pdf => {
                const option = document.createElement('option');
                option.value = pdf.path;
                option.textContent = `${pdf.filename} (${pdf.question_count} вопросов)`;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Ошибка загрузки списка PDF:', error);
    }
}

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

    container.innerHTML = quizzes.map(quiz => `
        <div class="question-card" style="margin-bottom: 15px;">
            <div class="question-header">
                <div>
                    <h3 style="margin-bottom: 5px;">${quiz.title}</h3>
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
                    <div style="display: flex; gap: 10px;">
                        <button onclick="copyQuizLink('${quiz.unique_code}')" class="btn-secondary" style="padding: 8px 15px;">
                            📋 Копировать ссылку
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
    `).join('');
}

// ==================== СОЗДАНИЕ ВИКТОРИНЫ ====================

function showPdfSelector() {
    document.getElementById('pdf-selector').style.display = 'block';
    document.getElementById('manual-selector').style.display = 'none';
    loadPDFListForQuiz();
}

function showManualSelector() {
    document.getElementById('pdf-selector').style.display = 'none';
    document.getElementById('manual-selector').style.display = 'block';
    updateSelectedQuestionsDisplay();
}

// Загрузить вопросы из выбранного PDF
async function loadQuestionsFromPdf() {
    const pdfPath = document.getElementById('pdf-select').value;

    if (!pdfPath) {
        document.getElementById('pdf-questions-preview').innerHTML = '';
        return;
    }

    try {
        const response = await fetch(`${API_URL}/questions/by-pdf?source_pdf=${encodeURIComponent(pdfPath)}`);
        const data = await response.json();

        if (data.success) {
            pdfQuestions = data.questions;

            document.getElementById('pdf-questions-preview').innerHTML = `
                <div style="padding: 15px; background: #f5f5f5; border-radius: 8px;">
                    <p><strong>Найдено вопросов:</strong> ${data.count}</p>
                    <p style="color: #666; margin-top: 5px;">Все вопросы из этого PDF будут добавлены в викторину</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Ошибка загрузки вопросов из PDF:', error);
    }
}

// Добавить вопрос в викторину (вызывается из displayQuestions)
function addQuestionToQuiz(questionId) {
    if (!selectedQuestions.includes(questionId)) {
        selectedQuestions.push(questionId);
        updateSelectedQuestionsDisplay();
        alert('✅ Вопрос добавлен в викторину');
    } else {
        alert('⚠️ Этот вопрос уже добавлен');
    }
}

// Удалить вопрос из викторины
function removeQuestionFromQuiz(questionId) {
    selectedQuestions = selectedQuestions.filter(id => id !== questionId);
    updateSelectedQuestionsDisplay();
}

// Обновить отображение выбранных вопросов
function updateSelectedQuestionsDisplay() {
    const container = document.getElementById('selected-questions');

    if (selectedQuestions.length === 0) {
        container.innerHTML = '<p style="color: #999;">Нет выбранных вопросов. Перейдите на вкладку "Просмотр вопросов" и добавьте вопросы.</p>';
        return;
    }

    container.innerHTML = `
        <div style="padding: 15px; background: #f5f5f5; border-radius: 8px;">
            <p><strong>Выбрано вопросов:</strong> ${selectedQuestions.length}</p>
            <div style="margin-top: 10px; display: flex; flex-wrap: wrap; gap: 5px;">
                ${selectedQuestions.map(id => `
                    <span class="tag" style="cursor: pointer;" onclick="removeQuestionFromQuiz(${id})">
                        Вопрос #${id} ✕
                    </span>
                `).join('')}
            </div>
        </div>
    `;
}

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

    // Определяем список вопросов
    let questionIds = [];

    if (pdfQuestions.length > 0) {
        // Из PDF
        questionIds = pdfQuestions.map(q => q.id);
    } else if (selectedQuestions.length > 0) {
        // Ручной выбор
        questionIds = selectedQuestions;
    } else {
        alert('❌ Добавьте хотя бы один вопрос в викторину');
        return;
    }

    // Создаем викторину через API
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
                question_ids: questionIds,
                max_attempts: maxAttempts,
                show_correct_answers: false,
                allow_review: true,
                pass_threshold: 0.0,
                shuffle_questions: false,
                shuffle_options: false
            })
        });

        const data = await response.json();

        if (data.success) {
            alert(`✅ Викторина создана!\n\nКод доступа: ${data.quiz.unique_code}\n\nСсылка: ${window.location.origin}/quiz.html?code=${data.quiz.unique_code}`);

            // Очищаем форму
            document.getElementById('quiz-title').value = '';
            document.getElementById('quiz-description').value = '';
            selectedQuestions = [];
            pdfQuestions = [];
            document.getElementById('pdf-select').value = '';
            document.getElementById('pdf-questions-preview').innerHTML = '';
            updateSelectedQuestionsDisplay();

            // Перезагружаем список викторин
            loadQuizzes();
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

// ==================== ИНИЦИАЛИЗАЦИЯ ====================

// Загрузить викторины при переключении на таб
window.addEventListener('DOMContentLoaded', () => {
    // Загружаем викторины при инициализации
    loadQuizzes();
});
