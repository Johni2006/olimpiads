// Конфигурация API
const API_URL = 'http://localhost:5001/api';

// Глобальное состояние
let currentTest = null;
let currentQuestionIndex = 0;
let testAnswers = [];

// =========================
// Инициализация
// =========================

async function init() {
    await loadFilters();
    await loadSourcePDFs();
    await loadQuestions();
    await loadStats();
}

// =========================
// Навигация по табам
// =========================

function switchTab(tabName) {
    // Скрываем все табы
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });

    // Показываем выбранный таб
    document.getElementById(tabName).classList.add('active');
    event.target.classList.add('active');

    // Загружаем данные для таба
    if (tabName === 'browse') {
        loadQuestions();
    } else if (tabName === 'stats') {
        loadStats();
    }
}

// =========================
// Загрузка фильтров
// =========================

async function loadFilters() {
    try {
        const response = await fetch(`${API_URL}/filters`);
        const data = await response.json();

        if (data.success) {
            const filters = data.filters;

            // Предметы
            populateSelect('filter-subject', filters.subjects);
            populateSelect('test-subject', filters.subjects);

            // Университеты
            populateSelect('filter-university', filters.universities);

            // Годы
            populateSelect('filter-year', filters.years);
        }
    } catch (error) {
        console.error('Ошибка загрузки фильтров:', error);
    }
}

async function loadSourcePDFs() {
    try {
        const response = await fetch(`${API_URL}/source-pdfs`);
        const data = await response.json();

        if (data.success && data.pdfs) {
            const select = document.getElementById('filter-source-pdf');
            const firstOption = select.options[0];

            // Очищаем
            select.innerHTML = '';
            select.appendChild(firstOption);

            // Добавляем PDF файлы
            data.pdfs.forEach(pdf => {
                const opt = document.createElement('option');
                opt.value = pdf.path;
                // Показываем только имя файла и количество вопросов
                const fileName = pdf.path.split('/').pop();
                opt.textContent = `${fileName} (${pdf.count} вопросов)`;
                select.appendChild(opt);
            });
        }
    } catch (error) {
        console.error('Ошибка загрузки списка PDF:', error);
    }
}

function populateSelect(selectId, options) {
    const select = document.getElementById(selectId);
    const currentValue = select.value;

    // Сохраняем первую опцию ("Все...")
    const firstOption = select.options[0];

    // Очищаем
    select.innerHTML = '';
    select.appendChild(firstOption);

    // Добавляем новые опции
    options.forEach(option => {
        const opt = document.createElement('option');
        opt.value = option;
        opt.textContent = option;
        select.appendChild(opt);
    });

    // Восстанавливаем выбранное значение
    select.value = currentValue;
}

// =========================
// Загрузка вопросов
// =========================

async function loadQuestions() {
    const container = document.getElementById('questions-container');
    container.innerHTML = '<div class="loading">Загрузка вопросов...</div>';

    try {
        const params = new URLSearchParams({
            limit: 50
        });

        const response = await fetch(`${API_URL}/questions?${params}`);
        const data = await response.json();

        if (data.success && data.questions.length > 0) {
            displayQuestions(data.questions);
        } else {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">📝</div>
                    <h3>Вопросы не найдены</h3>
                    <p>Попробуйте изменить фильтры или импортировать PDF файлы</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Ошибка загрузки вопросов:', error);
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">⚠️</div>
                <h3>Ошибка загрузки</h3>
                <p>${error.message}</p>
            </div>
        `;
    }
}

async function applyFilters() {
    const container = document.getElementById('questions-container');
    container.innerHTML = '<div class="loading">Применение фильтров...</div>';

    try {
        const params = new URLSearchParams({
            limit: 50
        });

        // Добавляем фильтры
        const sourcePdf = document.getElementById('filter-source-pdf').value;
        const subject = document.getElementById('filter-subject').value;
        const university = document.getElementById('filter-university').value;
        const year = document.getElementById('filter-year').value;
        const type = document.getElementById('filter-type').value;
        const difficulty = document.getElementById('filter-difficulty').value;
        const verified = document.getElementById('filter-verified').value;

        if (sourcePdf) params.append('source_pdf', sourcePdf);
        if (subject) params.append('subject', subject);
        if (university) params.append('university', university);
        if (year) params.append('year', year);
        if (type) params.append('question_type', type);
        if (difficulty) params.append('difficulty', difficulty);
        if (verified) params.append('verified', verified);

        const response = await fetch(`${API_URL}/questions?${params}`);
        const data = await response.json();

        if (data.success && data.questions.length > 0) {
            displayQuestions(data.questions);
        } else {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">🔍</div>
                    <h3>Ничего не найдено</h3>
                    <p>Попробуйте изменить параметры фильтрации</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Ошибка применения фильтров:', error);
    }
}

function displayQuestions(questions) {
    const container = document.getElementById('questions-container');

    container.innerHTML = questions.map((q, index) => {
        const tags = q.tags || {};
        const subjects = tags.subject || [];
        const universities = tags.university || [];
        const years = tags.year || [];

        return `
            <div class="question-card">
                <div class="question-header">
                    <div class="question-text">
                        <strong>Вопрос ${index + 1}:</strong> ${q.text}
                        ${q.verified ? '<span class="verified-badge">✓ Проверено</span>' : ''}
                    </div>
                    <div style="display: flex; gap: 10px;">
                        <button class="edit-btn" onclick="showEditModal(${q.id})">✏️ Редактировать</button>
                        ${q.source_pdf ? `
                            <a href="${API_URL}/pdf/${encodeURIComponent(q.source_pdf)}"
                               target="_blank"
                               class="view-pdf-btn"
                               title="Посмотреть исходный PDF">
                                📄 PDF
                            </a>
                        ` : ''}
                    </div>
                </div>

                <div class="question-meta">
                    ${subjects.map(s => `<span class="tag subject">${s}</span>`).join('')}
                    ${universities.map(u => `<span class="tag university">${u}</span>`).join('')}
                    ${years.map(y => `<span class="tag year">${y}</span>`).join('')}
                    ${q.difficulty ? `<span class="tag difficulty">Сложность: ${q.difficulty}</span>` : ''}
                    <span class="tag">Баллов: ${q.points || 1}</span>
                    <span class="tag">${getTypeLabel(q.type)}</span>
                </div>

                ${q.options && q.options.length > 0 ? `
                    <div class="options">
                        ${q.options.map((opt, i) => `
                            <div class="option ${opt.is_correct ? 'correct' : ''}">
                                ${i + 1}. ${opt.text}
                                ${opt.is_correct ? ' ✓' : ''}
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `;
    }).join('');
}

function getTypeLabel(type) {
    const labels = {
        'choice': 'Одиночный выбор',
        'multiple_choice': 'Множественный выбор',
        'matching': 'Соответствие',
        'text': 'Текстовый ответ'
    };
    return labels[type] || type;
}

// =========================
// Тестирование
// =========================

async function startTest() {
    const subject = document.getElementById('test-subject').value;
    const count = parseInt(document.getElementById('test-count').value) || 10;

    const container = document.getElementById('test-container');
    container.innerHTML = '<div class="loading">Загрузка теста...</div>';

    try {
        const params = new URLSearchParams({ count });
        if (subject) params.append('subject', subject);

        const response = await fetch(`${API_URL}/random?${params}`);
        const data = await response.json();

        if (data.success && data.questions.length > 0) {
            currentTest = data.questions;
            currentQuestionIndex = 0;
            testAnswers = new Array(currentTest.length).fill(null);
            displayTestQuestion();
        } else {
            container.innerHTML = `
                <div class="empty-state">
                    <h3>Недостаточно вопросов</h3>
                    <p>Выберите другой предмет или импортируйте больше вопросов</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Ошибка загрузки теста:', error);
    }
}

function displayTestQuestion() {
    const container = document.getElementById('test-container');
    const question = currentTest[currentQuestionIndex];
    const progress = ((currentQuestionIndex + 1) / currentTest.length * 100).toFixed(0);

    container.innerHTML = `
        <div class="progress-bar">
            <div class="progress-fill" style="width: ${progress}%">
                ${currentQuestionIndex + 1} / ${currentTest.length}
            </div>
        </div>

        <div class="question-card">
            <div class="question-text">
                <strong>Вопрос ${currentQuestionIndex + 1}:</strong> ${question.text}
            </div>

            ${question.options && question.options.length > 0 ? `
                <div class="options">
                    ${question.options.map((opt, i) => `
                        <div class="option" onclick="selectOption(${i})" data-option-index="${i}">
                            ${i + 1}. ${opt.text}
                        </div>
                    `).join('')}
                </div>
            ` : ''}

            <div style="margin-top: 20px; display: flex; gap: 10px;">
                ${currentQuestionIndex > 0 ? `
                    <button onclick="previousQuestion()">← Назад</button>
                ` : ''}
                ${currentQuestionIndex < currentTest.length - 1 ? `
                    <button onclick="nextQuestion()">Далее →</button>
                ` : `
                    <button onclick="finishTest()">✓ Завершить тест</button>
                `}
            </div>
        </div>
    `;
}

function selectOption(optionIndex) {
    // Убираем выделение со всех опций
    document.querySelectorAll('.option').forEach(opt => {
        opt.classList.remove('selected');
    });

    // Выделяем выбранную опцию
    const selectedOption = document.querySelector(`[data-option-index="${optionIndex}"]`);
    selectedOption.classList.add('selected');

    // Сохраняем ответ
    const question = currentTest[currentQuestionIndex];
    testAnswers[currentQuestionIndex] = question.options[optionIndex].text;
}

function nextQuestion() {
    if (currentQuestionIndex < currentTest.length - 1) {
        currentQuestionIndex++;
        displayTestQuestion();
    }
}

function previousQuestion() {
    if (currentQuestionIndex > 0) {
        currentQuestionIndex--;
        displayTestQuestion();
    }
}

async function finishTest() {
    const container = document.getElementById('test-container');
    container.innerHTML = '<div class="loading">Проверка ответов...</div>';

    let correctCount = 0;

    // Проверяем каждый ответ
    for (let i = 0; i < currentTest.length; i++) {
        const question = currentTest[i];
        const userAnswer = testAnswers[i];

        if (userAnswer) {
            try {
                const response = await fetch(`${API_URL}/check_answer`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        question_id: question.id,
                        answer: userAnswer
                    })
                });

                const data = await response.json();
                if (data.success && data.is_correct) {
                    correctCount++;
                }
            } catch (error) {
                console.error('Ошибка проверки ответа:', error);
            }
        }
    }

    // Показываем результаты
    const percentage = (correctCount / currentTest.length * 100).toFixed(0);

    container.innerHTML = `
        <div class="test-result">
            <h2>🎉 Тест завершён!</h2>
            <div class="score">${percentage}%</div>
            <p style="font-size: 1.3em; margin: 20px 0;">
                Правильных ответов: <strong>${correctCount}</strong> из <strong>${currentTest.length}</strong>
            </p>
            <button onclick="startTest()">🔄 Пройти ещё раз</button>
        </div>
    `;
}

// =========================
// Статистика
// =========================

async function loadStats() {
    const container = document.getElementById('stats-container');
    container.innerHTML = '<div class="loading">Загрузка статистики...</div>';

    try {
        const response = await fetch(`${API_URL}/stats`);
        const data = await response.json();

        if (data.success) {
            displayStats(data.stats);
        }
    } catch (error) {
        console.error('Ошибка загрузки статистики:', error);
    }
}

function displayStats(stats) {
    const container = document.getElementById('stats-container');

    let html = `
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Всего вопросов</div>
                <div class="stat-number">${stats.total_questions || 0}</div>
            </div>
        </div>

        <h3 style="margin-top: 30px;">По предметам:</h3>
        <div class="stats-grid">
            ${Object.entries(stats.by_subject || {}).map(([subject, count]) => `
                <div class="stat-card">
                    <div class="stat-label">${subject}</div>
                    <div class="stat-number">${count}</div>
                </div>
            `).join('')}
        </div>

        <h3 style="margin-top: 30px;">По университетам:</h3>
        <div class="stats-grid">
            ${Object.entries(stats.by_university || {}).map(([uni, count]) => `
                <div class="stat-card">
                    <div class="stat-label">${uni}</div>
                    <div class="stat-number">${count}</div>
                </div>
            `).join('')}
        </div>
    `;

    container.innerHTML = html;
}

// =========================
// Запуск при загрузке
// =========================

window.addEventListener('DOMContentLoaded', init);