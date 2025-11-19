// Конфигурация API
const API_URL = 'http://localhost:5001/api';

console.log('=== app.js загружен ===');
window.APP_VERSION = '4.0';

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
    await loadPDFFilters();  // Загружаем фильтры для PDF
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
    } else if (tabName === 'pdfs') {
        loadPDFList();
    } else if (tabName === 'admin') {
        loadAdminStats();
        loadSourcesList();
        loadDownloaderStats();
        loadSubjectsList();
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

async function loadPDFFilters() {
    try {
        // Получаем все PDF файлы для заполнения фильтров
        const response = await fetch(`${API_URL}/pdfs?limit=1000`);
        const data = await response.json();

        if (data.success && data.pdfs) {
            // Собираем уникальные значения
            const universities = new Set();
            const subjects = new Set();
            const years = new Set();

            data.pdfs.forEach(pdf => {
                if (pdf.university) universities.add(pdf.university);
                if (pdf.subject) subjects.add(pdf.subject);
                if (pdf.year) years.add(pdf.year);
            });

            // Заполняем селекты
            populateSelect('pdf-filter-university', Array.from(universities).sort());
            populateSelect('pdf-filter-subject', Array.from(subjects).sort());
            populateSelect('pdf-filter-year', Array.from(years).sort().reverse());

            // Заполняем фильтр "Исходный PDF" списком всех PDF файлов
            const pdfSourceSelect = document.getElementById('pdf-filter-source');
            if (pdfSourceSelect) {
                const firstOption = pdfSourceSelect.options[0];
                pdfSourceSelect.innerHTML = '';
                pdfSourceSelect.appendChild(firstOption);

                // Сортируем по display_name и добавляем
                const sortedPdfs = data.pdfs.sort((a, b) =>
                    (a.display_name || a.file_path).localeCompare(b.display_name || b.file_path)
                );

                sortedPdfs.forEach(pdf => {
                    const opt = document.createElement('option');
                    opt.value = pdf.display_name || pdf.file_path;
                    opt.textContent = `${pdf.display_name || pdf.file_path} (${pdf.question_count || 0} вопросов)`;
                    pdfSourceSelect.appendChild(opt);
                });
            }
        }
    } catch (error) {
        console.error('Ошибка загрузки фильтров PDF:', error);
    }
}

function populateSelect(selectId, options) {
    const select = document.getElementById(selectId);
    if (!select) {
        console.warn(`Select element with id "${selectId}" not found`);
        return;
    }

    const currentValue = select.value;

    // Сохраняем первую опцию ("Все...")
    const firstOption = select.options[0];

    // Очищаем
    select.innerHTML = '';
    if (firstOption) {
        select.appendChild(firstOption);
    }

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
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <button class="edit-btn" onclick="showEditQuestionModal(${q.id})">✏️ Редактировать</button>
                        ${q.source_pdf ? `
                            <a href="${API_URL}/pdf/${encodeURIComponent(q.source_pdf)}"
                               target="_blank"
                               class="view-pdf-btn"
                               title="Посмотреть исходный PDF">
                                📄 PDF
                            </a>
                        ` : ''}
                        <button class="btn-danger" style="padding: 8px 15px; font-size: 0.9em;" onclick="deleteQuestionFromList(${q.id})" title="Удалить вопрос">
                            🗑️
                        </button>
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

// Функция для редактирования вопроса из списка
function showEditQuestionModal(questionId) {
    // Используем функцию из edit.js
    // Функция showEditModal загружается из edit.js после app.js
    // К моменту клика пользователя скрипты уже загружены
    setTimeout(() => {
        if (typeof window.showEditModal === 'function') {
            window.showEditModal(questionId);
        } else {
            console.error('showEditModal не загружена');
            // Пробуем загрузить скрипт заново
            const script = document.createElement('script');
            script.src = 'edit.js?v=' + Date.now();
            script.onload = () => {
                if (typeof window.showEditModal === 'function') {
                    window.showEditModal(questionId);
                } else {
                    alert('Ошибка загрузки функции редактирования. Перезагрузите страницу (Ctrl+F5)');
                }
            };
            document.body.appendChild(script);
        }
    }, 10);
}

// Функция для удаления вопроса из списка
async function deleteQuestionFromList(questionId) {
    if (!confirm('❌ Вы уверены, что хотите удалить этот вопрос?\n\nЭто действие нельзя отменить!')) {
        return;
    }

    try {
        const response = await fetch(`${API_URL}/questions/${questionId}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            alert('✅ Вопрос успешно удалён!');
            // Перезагружаем список вопросов
            applyFilters();
        } else {
            alert('❌ Ошибка: ' + result.error);
        }
    } catch (error) {
        console.error('Ошибка удаления вопроса:', error);
        alert('❌ Ошибка удаления вопроса');
    }
}

// Функция для добавления вопроса со страницы просмотра
function addQuestionFromBrowse() {
    // Вызываем функцию добавления вопроса без привязки к PDF
    addNewQuestion(null, null);
}

function getTypeLabel(type) {
    const labels = {
        'choice': 'Одиночный выбор',
        'multiple_choice': 'Множественный выбор',
        'matching': 'Соответствие',
        'text': 'Текстовый ответ',
        'essay': 'Эссе'
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
// Управление PDF файлами
// =========================

async function loadPDFList() {
    try {
        const container = document.getElementById('pdf-list-container');
        if (!container) {
            console.error('Контейнер pdf-list-container не найден!');
            return;
        }
        container.innerHTML = '<div class="loading">Загрузка списка PDF...</div>';

        const params = new URLSearchParams();
        params.append('limit', '1000'); // Загружаем до 1000 файлов

        const university = document.getElementById('pdf-filter-university')?.value;
        const subject = document.getElementById('pdf-filter-subject')?.value;
        const year = document.getElementById('pdf-filter-year')?.value;
        const search = document.getElementById('pdf-search')?.value;
        const sourcePdf = document.getElementById('pdf-filter-source')?.value;

        if (university) params.append('university', university);
        if (subject) params.append('subject', subject);
        if (year) params.append('year', year);
        if (search) params.append('search', search);
        if (sourcePdf) params.append('search', sourcePdf); // Используем search для фильтра по имени

        const response = await fetch(`${API_URL}/pdfs?${params}`);
        const data = await response.json();

        if (data.success && data.pdfs.length > 0) {
            displayPDFList(data.pdfs);
        } else {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">📄</div>
                    <h3>PDF файлы не найдены</h3>
                    <p>Загрузите PDF файлы с помощью формы выше</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Ошибка загрузки PDF:', error);
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">⚠️</div>
                <h3>Ошибка загрузки</h3>
                <p>${error.message}</p>
            </div>
        `;
    }
}

function displayPDFList(pdfs) {
    const container = document.getElementById('pdf-list-container');

    container.innerHTML = `
        <div style="background: #e3f2fd; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            <strong>📊 Найдено файлов:</strong> ${pdfs.length}
        </div>
        <div style="margin-top: 20px;">
            ${pdfs.map(pdf => {
                const statusClass = pdf.verification_status === 'verified' ? 'status-verified' :
                                   pdf.verification_status === 'partially_verified' ? 'status-partially-verified' :
                                   'status-not-verified';
                const statusColor = pdf.verification_status === 'verified' ? 'green' :
                                   pdf.verification_status === 'partially_verified' ? 'yellow' :
                                   'red';
                return `
                <div class="question-card" style="margin-bottom: 15px;">
                    <div style="display: flex; justify-content: space-between; align-items: start; gap: 20px;">
                        <div style="flex: 1;">
                            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                                <h4 style="margin: 0;">${pdf.display_name || pdf.file_path}</h4>
                                <span class="status-badge ${statusClass}">
                                    <span class="status-indicator ${statusColor}"></span>
                                    ${getVerificationLabel(pdf.verification_status)}
                                </span>
                                ${pdf.is_manual ? '<span class="tag" style="background: #9c27b0; color: white;">📤 Загружен вручную</span>' : ''}
                            </div>
                            <div class="question-meta">
                                ${pdf.university ? `<span class="tag university">${pdf.university}</span>` : ''}
                                ${pdf.subject ? `<span class="tag subject">${pdf.subject}</span>` : ''}
                                ${pdf.year ? `<span class="tag year">${pdf.year}</span>` : ''}
                                ${pdf.olympiad ? `<span class="tag">${pdf.olympiad}</span>` : ''}
                                <span class="tag">Вопросов: ${pdf.question_count || 0}</span>
                            </div>
                            <div style="margin-top: 10px; font-size: 0.9em; color: #666;">
                                <strong>Путь:</strong> ${pdf.file_path}
                            </div>
                        </div>
                        <div style="display: flex; flex-direction: column; gap: 8px;">
                            <button onclick="editPDF(${pdf.id})" class="edit-btn" style="background: #4caf50;">
                                ✏️ Редактировать
                            </button>
                            <a href="${API_URL}/pdf/${encodeURIComponent(pdf.file_path)}" target="_blank" class="edit-btn" style="background: #2196f3; text-decoration: none; text-align: center; display: inline-block;">
                                📄 PDF
                            </a>
                            <button onclick="reparsePDF(${pdf.id})" class="edit-btn" style="background: #9c27b0;">
                                🔄 Перепарсить
                            </button>
                            <button onclick="viewPDFQuestions(${pdf.id})" class="edit-btn" style="background: #ff9800;">
                                📝 Вопросы
                            </button>
                            <button onclick="deletePDFFile(${pdf.id})" class="btn-danger" style="padding: 8px 15px; font-size: 0.9em;">
                                🗑️ Удалить файл
                            </button>
                        </div>
                    </div>
                </div>
            `}).join('')}
        </div>
    `;
}

function getVerificationLabel(status) {
    const labels = {
        'verified': '✓ Проверено',
        'partially_verified': '⚠ Частично проверено',
        'not_verified': '✗ Не проверено'
    };
    return labels[status] || status;
}

async function reparsePDF(pdfId) {
    if (!confirm('Перепарсить PDF файл? Это может занять некоторое время.')) {
        return;
    }

    try {
        const response = await fetch(`${API_URL}/pdfs/${pdfId}/reparse`, {
            method: 'POST'
        });
        const data = await response.json();

        if (data.success) {
            const apply = confirm(
                `Найдено ${data.preview.questions_found} вопросов. ` +
                `Сейчас в БД: ${data.preview.existing_questions_count}.\n\n` +
                `Применить результаты перепарсинга?\n` +
                `(OK = заменить все, Отмена = добавить новые)`
            );

            if (apply !== null) {
                const strategy = apply ? 'replace_all' : 'add_new';
                await applyReparse(pdfId, strategy);
            }
        } else {
            alert('Ошибка: ' + data.error);
        }
    } catch (error) {
        console.error('Ошибка перепарсинга:', error);
        alert('Ошибка: ' + error.message);
    }
}

async function applyReparse(pdfId, strategy) {
    try {
        const response = await fetch(`${API_URL}/pdfs/${pdfId}/apply-reparse`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ strategy })
        });
        const data = await response.json();

        if (data.success) {
            alert(`✓ Успешно! ${data.message}`);
            loadPDFList();
        } else {
            alert('Ошибка: ' + data.error);
        }
    } catch (error) {
        console.error('Ошибка применения перепарсинга:', error);
        alert('Ошибка: ' + error.message);
    }
}

async function editPDF(pdfId) {
    try {
        // Получаем текущие данные PDF
        const response = await fetch(`${API_URL}/pdfs/${pdfId}`);
        const data = await response.json();

        if (!data.success) {
            alert('Ошибка загрузки PDF: ' + data.error);
            return;
        }

        const pdf = data.pdf;

        // Создаем модальное окно
        const modal = document.getElementById('edit-modal');
        modal.style.display = 'flex';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Редактирование PDF: ${pdf.display_name}</h2>
                    <div style="display: flex; gap: 10px; align-items: center;">
                        ${pdf.file_path && !pdf.is_manual ? `
                            <a href="${API_URL}/pdf/${encodeURIComponent(pdf.file_path)}"
                               target="_blank"
                               class="view-pdf-btn"
                               title="Посмотреть PDF файл">
                                📄 PDF
                            </a>
                        ` : ''}
                        <button class="close-btn" onclick="closeEditModal()">&times;</button>
                    </div>
                </div>
                <div class="modal-body">
                    <form id="edit-pdf-form">
                        <div class="form-group">
                            <label>Отображаемое имя</label>
                            <input type="text" id="edit-display-name" value="${pdf.display_name || ''}" required>
                        </div>

                        <div class="form-row">
                            <div class="form-group">
                                <label>Университет</label>
                                <input type="text" id="edit-university" value="${pdf.university || ''}">
                            </div>
                            <div class="form-group">
                                <label>Олимпиада</label>
                                <input type="text" id="edit-olympiad" value="${pdf.olympiad || ''}">
                            </div>
                        </div>

                        <div class="form-row">
                            <div class="form-group">
                                <label>Предмет</label>
                                <input type="text" id="edit-subject" value="${pdf.subject || ''}">
                            </div>
                            <div class="form-group">
                                <label>Год</label>
                                <input type="text" id="edit-year" value="${pdf.year || ''}">
                            </div>
                        </div>

                        <div class="form-group">
                            <label>Статус проверки</label>
                            <select id="edit-verification-status">
                                <option value="not_verified" ${pdf.verification_status === 'not_verified' ? 'selected' : ''}>Не проверено</option>
                                <option value="partially_verified" ${pdf.verification_status === 'partially_verified' ? 'selected' : ''}>Частично проверено</option>
                                <option value="verified" ${pdf.verification_status === 'verified' ? 'selected' : ''}>Проверено</option>
                            </select>
                        </div>

                        <div class="form-group">
                            <label>Способ загрузки</label>
                            <div style="padding: 10px; background: ${pdf.is_manual ? '#e3f2fd' : '#f5f5f5'}; border-radius: 4px; border-left: 4px solid ${pdf.is_manual ? '#2196f3' : '#9e9e9e'};">
                                ${pdf.is_manual ? '📤 Загружен вручную' : '🤖 Загружен автоматически'}
                            </div>
                        </div>

                        <label class="checkbox-label">
                            <input type="checkbox" id="edit-cascade" checked>
                            Обновить теги у всех вопросов из этого PDF
                        </label>

                        <div class="form-actions">
                            <button type="submit" class="btn-primary">💾 Сохранить изменения</button>
                            <button type="button" class="btn-secondary" onclick="closeEditModal()">Отмена</button>
                            <button type="button" class="btn-danger" onclick="deletePDFFile(${pdfId})" style="margin-left: auto;">🗑️ Удалить файл</button>
                        </div>
                    </form>
                </div>
            </div>
        `;

        // Обработчик формы
        document.getElementById('edit-pdf-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            await savePDFChanges(pdfId);
        });

    } catch (error) {
        console.error('Ошибка открытия редактирования:', error);
        alert('Ошибка: ' + error.message);
    }
}

async function savePDFChanges(pdfId) {
    try {
        const updateData = {
            display_name: document.getElementById('edit-display-name').value,
            university: document.getElementById('edit-university').value,
            olympiad: document.getElementById('edit-olympiad').value,
            subject: document.getElementById('edit-subject').value,
            year: document.getElementById('edit-year').value,
            cascade_to_questions: document.getElementById('edit-cascade').checked
        };

        // Обновляем метаданные
        const response = await fetch(`${API_URL}/pdfs/${pdfId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updateData)
        });

        const data = await response.json();

        if (data.success) {
            // Обновляем статус проверки отдельно
            const verificationStatus = document.getElementById('edit-verification-status').value;
            await fetch(`${API_URL}/pdfs/${pdfId}/verification-status`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ status: verificationStatus })
            });

            alert('✓ Изменения сохранены!');
            closeEditModal();
            loadPDFList();
        } else {
            alert('Ошибка: ' + data.error);
        }
    } catch (error) {
        console.error('Ошибка сохранения:', error);
        alert('Ошибка: ' + error.message);
    }
}

async function deletePDFFile(pdfId) {
    if (!confirm('❌ Вы уверены, что хотите удалить этот PDF файл?\n\nЭто действие также удалит ВСЕ связанные вопросы из этого файла!')) {
        return;
    }

    try {
        const response = await fetch(`${API_URL}/pdfs/${pdfId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            alert(`✅ PDF файл удалён!\nУдалено вопросов: ${data.questions_deleted || 0}`);
            closeEditModal();
            loadPDFList();
        } else {
            alert('❌ Ошибка: ' + data.error);
        }
    } catch (error) {
        console.error('Ошибка удаления:', error);
        alert('❌ Ошибка удаления: ' + error.message);
    }
}

// Функция closeEditModal определена в edit.js и переопределит эту
// Оставляем заглушку на случай, если edit.js не загрузится
function closeEditModal() {
    const modal = document.getElementById('edit-modal');
    if (modal) {
        modal.style.display = 'none';
        modal.innerHTML = '';
    }
}

async function viewPDFQuestions(pdfId) {
    try {
        // Получаем информацию о PDF
        const pdfResponse = await fetch(`${API_URL}/pdfs/${pdfId}`);
        const pdfData = await pdfResponse.json();

        if (!pdfData.success) {
            alert('Ошибка загрузки PDF');
            return;
        }

        const pdf = pdfData.pdf;

        // Получаем вопросы из этого PDF
        const questionsResponse = await fetch(`${API_URL}/questions/by-pdf?source_pdf=${encodeURIComponent(pdf.file_path)}`);
        const questionsData = await questionsResponse.json();

        if (!questionsData.success) {
            alert('Ошибка загрузки вопросов');
            return;
        }

        // Подсчитываем статистику
        const verifiedCount = questionsData.questions.filter(q => q.verified).length;
        const unverifiedCount = questionsData.count - verifiedCount;
        const verificationPercent = Math.round((verifiedCount / questionsData.count) * 100);

        // Создаем модальное окно с вопросами
        const modal = document.getElementById('edit-modal');
        modal.style.display = 'flex';
        modal.innerHTML = `
            <div class="modal-content" style="max-width: 1200px;">
                <div class="modal-header">
                    <h2>Вопросы из: ${pdf.display_name}</h2>
                    <div style="display: flex; gap: 10px; align-items: center;">
                        ${pdf.file_path && !pdf.is_manual ? `
                            <a href="${API_URL}/pdf/${encodeURIComponent(pdf.file_path)}"
                               target="_blank"
                               class="view-pdf-btn"
                               title="Открыть PDF файл">
                                📄 Открыть PDF
                            </a>
                        ` : ''}
                        <button class="close-btn" onclick="closeEditModal()">&times;</button>
                    </div>
                </div>
                <div class="modal-body">
                    <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                        <strong>📊 Статистика проверки:</strong><br>
                        Всего вопросов: ${questionsData.count} |
                        ✓ Проверено: ${verifiedCount} (${verificationPercent}%) |
                        ✗ Не проверено: ${unverifiedCount}
                    </div>
                    <div style="max-height: 600px; overflow-y: auto;">
                        ${questionsData.questions.map((q, idx) => `
                            <div class="question-card" style="margin-bottom: 15px;">
                                <div style="display: flex; justify-content: space-between; gap: 20px;">
                                    <div style="flex: 1;">
                                        <div class="question-text">
                                            <strong>${idx + 1}.</strong> ${q.text.substring(0, 300)}${q.text.length > 300 ? '...' : ''}
                                        </div>
                                        <div class="question-meta" style="margin-top: 10px;">
                                            <span class="tag">${getTypeLabel(q.type)}</span>
                                            ${q.verified ? '<span class="tag correct">✓ Проверено</span>' : '<span class="tag incorrect">✗ Не проверено</span>'}
                                            ${q.difficulty ? `<span class="tag difficulty">Сложность: ${q.difficulty}</span>` : ''}
                                        </div>
                                    </div>
                                    <div style="display: flex; gap: 5px;">
                                        <button class="edit-btn" onclick="editQuestionFromPDF(${q.id}, ${pdfId})" style="white-space: nowrap;">
                                            ✏️ Редактировать
                                        </button>
                                        ${q.source_pdf ? `
                                            <a href="${API_URL}/pdf/${encodeURIComponent(q.source_pdf)}"
                                               target="_blank"
                                               class="view-pdf-btn"
                                               style="padding: 8px 12px; font-size: 0.9em;"
                                               title="Открыть PDF">
                                                📄
                                            </a>
                                        ` : ''}
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                    <div style="margin-top: 20px; text-align: center;">
                        <button class="btn-primary" onclick="addNewQuestion(${pdfId}, '${pdf.file_path.replace(/'/g, "\\'")}')">
                            ➕ Добавить новый вопрос
                        </button>
                    </div>
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Ошибка просмотра вопросов:', error);
        alert('Ошибка: ' + error.message);
    }
}

// Редактирование вопроса из просмотра PDF
async function editQuestionFromPDF(questionId, pdfId) {
    // Сохраняем pdfId для обновления после редактирования
    window.currentPdfId = pdfId;

    // Вызываем wrapper функцию для редактирования
    showEditQuestionModal(questionId);

    // После закрытия модального окна редактирования, обновляем список вопросов
    // Это будет обработано в edit.js при сохранении
}

// Функция для обновления списка вопросов PDF после редактирования
async function refreshPDFQuestions() {
    if (window.currentPdfId) {
        await viewPDFQuestions(window.currentPdfId);
        await loadPDFList(); // Обновляем также список PDF для обновления статуса
    }
}

// Добавить новый вопрос
function addNewQuestion(pdfId = null, sourcePdf = null) {
    const modal = document.getElementById('edit-modal');
    modal.style.display = 'flex';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2>➕ Создание нового вопроса</h2>
                <button class="close-btn" onclick="closeEditModal()">✕</button>
            </div>
            <div class="modal-body">
                <form id="new-question-form">
                    <div class="form-group">
                        <label>Текст вопроса:</label>
                        <textarea id="new-text" rows="4" required></textarea>
                    </div>

                    <!-- Изображения к вопросу -->
                    <div class="form-group">
                        <label>Изображения к вопросу:</label>
                        <div style="padding: 15px; background-color: #f8f9fa; border-radius: 8px; border-left: 4px solid #17a2b8;">
                            <p style="margin: 0; color: #666;">
                                💡 <strong>Совет:</strong> Сначала создайте вопрос, затем откройте его для редактирования, чтобы добавить изображения.
                            </p>
                            <p style="margin: 5px 0 0 0; font-size: 0.9em; color: #888;">
                                Изображения будут отображаться над текстом вопроса.
                            </p>
                        </div>
                    </div>

                    <div class="form-group">
                        <label>Тип вопроса:</label>
                        <select id="new-type" onchange="updateNewQuestionTypeFields()">
                            <option value="choice">Одиночный выбор</option>
                            <option value="multiple_choice">Множественный выбор</option>
                            <option value="matching">Соответствие</option>
                            <option value="text">Текстовый ответ</option>
                            <option value="essay">Эссе</option>
                        </select>
                    </div>

                    <div class="form-row">
                        <div class="form-group">
                            <label>Сложность (1-5):</label>
                            <input type="number" id="new-difficulty" min="1" max="5" value="1">
                        </div>
                        <div class="form-group">
                            <label>Баллы:</label>
                            <input type="number" id="new-points" step="0.5" value="1">
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="form-group">
                            <label>Предмет:</label>
                            <input type="text" id="new-subject">
                        </div>
                        <div class="form-group">
                            <label>Университет:</label>
                            <input type="text" id="new-university">
                        </div>
                    </div>

                    <div class="form-group">
                        <label>Год:</label>
                        <input type="text" id="new-year">
                    </div>

                    <div id="new-options-container">
                        <label>Варианты ответов:</label>
                        <div id="new-options">
                            <div class="option-edit">
                                <input type="checkbox" id="new-opt-correct-0">
                                <input type="text" id="new-opt-text-0" placeholder="Вариант 1">
                                <button type="button" onclick="removeNewOption(0)">✕</button>
                            </div>
                        </div>
                        <button type="button" onclick="addNewOption()" class="btn-secondary">+ Добавить вариант</button>
                    </div>

                    <div id="new-essay-container" style="display: none;">
                        <div class="form-group">
                            <label>Рекомендации по оцениванию:</label>
                            <textarea id="new-essay-guidelines" rows="8" placeholder="Опишите критерии оценивания..."></textarea>
                        </div>
                    </div>

                    <input type="hidden" id="new-source-pdf" value="${sourcePdf || ''}">
                    <input type="hidden" id="new-pdf-id" value="${pdfId || ''}">

                    <div class="form-actions">
                        <button type="button" onclick="saveNewQuestion()" class="btn-primary">💾 Создать вопрос</button>
                        <button type="button" onclick="closeEditModal()" class="btn-secondary">Отмена</button>
                    </div>
                </form>
            </div>
        </div>
    `;
}

// Обновить поля формы нового вопроса при изменении типа
function updateNewQuestionTypeFields() {
    const type = document.getElementById('new-type').value;
    const optionsContainer = document.getElementById('new-options-container');
    const essayContainer = document.getElementById('new-essay-container');

    if (type === 'choice' || type === 'multiple_choice') {
        optionsContainer.style.display = 'block';
        essayContainer.style.display = 'none';
    } else if (type === 'essay') {
        optionsContainer.style.display = 'none';
        essayContainer.style.display = 'block';
    } else {
        optionsContainer.style.display = 'none';
        essayContainer.style.display = 'none';
    }
}

// Добавить вариант ответа в новом вопросе
function addNewOption() {
    const container = document.getElementById('new-options');
    const count = container.children.length;

    const optionDiv = document.createElement('div');
    optionDiv.className = 'option-edit';
    optionDiv.innerHTML = `
        <input type="checkbox" id="new-opt-correct-${count}">
        <input type="text" id="new-opt-text-${count}" placeholder="Вариант ${count + 1}">
        <button type="button" onclick="removeNewOption(${count})">✕</button>
    `;
    container.appendChild(optionDiv);
}

// Удалить вариант ответа в новом вопросе
function removeNewOption(index) {
    const option = document.getElementById(`new-opt-text-${index}`);
    if (option) option.parentElement.remove();
}

// Сохранить новый вопрос
async function saveNewQuestion() {
    const data = {
        text: document.getElementById('new-text').value,
        type: document.getElementById('new-type').value,
        difficulty: parseInt(document.getElementById('new-difficulty').value),
        points: parseFloat(document.getElementById('new-points').value),
        verified: false,
        tags: {
            subject: [document.getElementById('new-subject').value].filter(v => v),
            university: [document.getElementById('new-university').value].filter(v => v),
            year: [document.getElementById('new-year').value].filter(v => v)
        },
        options: [],
        source_pdf: document.getElementById('new-source-pdf').value || null
    };

    // Собираем варианты ответов
    const optionsContainer = document.getElementById('new-options');
    if (optionsContainer && (data.type === 'choice' || data.type === 'multiple_choice')) {
        const optionDivs = optionsContainer.querySelectorAll('.option-edit');
        optionDivs.forEach((div, i) => {
            const textInput = div.querySelector(`#new-opt-text-${i}`);
            const correctCheckbox = div.querySelector(`#new-opt-correct-${i}`);

            if (textInput && textInput.value.trim()) {
                data.options.push({
                    text: textInput.value.trim(),
                    is_correct: correctCheckbox ? correctCheckbox.checked : false
                });
            }
        });
    }

    // Для эссе сохраняем рекомендации
    if (data.type === 'essay') {
        const guidelines = document.getElementById('new-essay-guidelines');
        if (guidelines && guidelines.value.trim()) {
            data.options.push({
                text: guidelines.value.trim(),
                is_correct: false
            });
        }
    }

    // ВАЛИДАЦИЯ: проверяем наличие вариантов ответа для типов choice/multiple_choice
    if ((data.type === 'choice' || data.type === 'multiple_choice') && data.options.length === 0) {
        alert('⚠️ Вопрос типа "Одиночный выбор" или "Множественный выбор" должен иметь хотя бы один вариант ответа!');
        return;
    }

    try {
        const response = await fetch(`${API_URL}/questions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            alert('✅ Вопрос успешно создан!');
            closeEditModal();

            // Обновляем список
            const pdfId = document.getElementById('new-pdf-id').value;
            if (pdfId) {
                await refreshPDFQuestions();
            } else if (typeof applyFilters === 'function') {
                applyFilters();
            }
        } else {
            alert('❌ Ошибка: ' + result.error);
        }
    } catch (error) {
        console.error('Ошибка создания вопроса:', error);
        alert('❌ Ошибка создания вопроса');
    }
}

// Обработка загрузки PDF
document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('upload-pdf-form');
    if (uploadForm) {
        uploadForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const fileInput = document.getElementById('pdf-file');
            const file = fileInput.files[0];

            if (!file) {
                alert('Выберите PDF файл');
                return;
            }

            const formData = new FormData();
            formData.append('file', file);
            formData.append('display_name', document.getElementById('pdf-display-name').value || file.name);
            formData.append('university', document.getElementById('pdf-university').value);
            formData.append('olympiad', document.getElementById('pdf-olympiad').value);
            formData.append('subject', document.getElementById('pdf-subject').value);
            formData.append('year', document.getElementById('pdf-year').value);

            const statusDiv = document.getElementById('upload-status');
            statusDiv.innerHTML = '<div class="loading">Загрузка и парсинг файла...</div>';

            try {
                const response = await fetch(`${API_URL}/pdfs/upload`, {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (data.success) {
                    statusDiv.innerHTML = `
                        <div style="padding: 15px; background: #e8f5e9; border-radius: 8px; color: #2e7d32;">
                            <strong>✓ Успешно!</strong><br>
                            ${data.message}<br>
                            Вопросов найдено: ${data.questions_parsed}
                        </div>
                    `;
                    uploadForm.reset();
                    loadPDFList();
                } else {
                    statusDiv.innerHTML = `
                        <div style="padding: 15px; background: #ffebee; border-radius: 8px; color: #c62828;">
                            <strong>✗ Ошибка:</strong> ${data.error || data.message}
                        </div>
                    `;
                }
            } catch (error) {
                console.error('Ошибка загрузки PDF:', error);
                statusDiv.innerHTML = `
                    <div style="padding: 15px; background: #ffebee; border-radius: 8px; color: #c62828;">
                        <strong>✗ Ошибка:</strong> ${error.message}
                    </div>
                `;
            }
        });
    }
});

// =========================
// Администрирование
// =========================

async function createBackup() {
    const statusDiv = document.getElementById('backup-status');
    statusDiv.innerHTML = '<div class="loading">Создание бэкапа...</div>';

    try {
        const response = await fetch(`${API_URL}/admin/backup`, {
            method: 'POST'
        });
        const data = await response.json();

        if (data.success) {
            statusDiv.innerHTML = `
                <div style="padding: 10px; background: #e8f5e9; border-radius: 6px; color: #2e7d32;">
                    <strong>✓ Успешно!</strong><br>
                    Бэкап создан: ${data.backup_file || 'файл сохранён'}
                </div>
            `;
        } else {
            statusDiv.innerHTML = `
                <div style="padding: 10px; background: #ffebee; border-radius: 6px; color: #c62828;">
                    <strong>✗ Ошибка:</strong> ${data.error}
                </div>
            `;
        }
    } catch (error) {
        console.error('Ошибка создания бэкапа:', error);
        statusDiv.innerHTML = `
            <div style="padding: 10px; background: #ffebee; border-radius: 6px; color: #c62828;">
                <strong>✗ Ошибка:</strong> ${error.message}
            </div>
        `;
    }
}

async function syncDatabase() {
    const statusDiv = document.getElementById('sync-status');
    statusDiv.innerHTML = '<div class="loading">Синхронизация...</div>';

    try {
        const response = await fetch(`${API_URL}/admin/sync-db`, {
            method: 'POST'
        });
        const data = await response.json();

        if (data.success) {
            statusDiv.innerHTML = `
                <div style="padding: 10px; background: #e8f5e9; border-radius: 6px; color: #2e7d32;">
                    <strong>✓ Синхронизация выполнена!</strong>
                </div>
            `;
        } else {
            statusDiv.innerHTML = `
                <div style="padding: 10px; background: #ffebee; border-radius: 6px; color: #c62828;">
                    <strong>✗ Ошибка:</strong> ${data.error}
                </div>
            `;
        }
    } catch (error) {
        console.error('Ошибка синхронизации:', error);
        statusDiv.innerHTML = `
            <div style="padding: 10px; background: #ffebee; border-radius: 6px; color: #c62828;">
                <strong>✗ Ошибка:</strong> ${error.message}
            </div>
        `;
    }
}

// =========================
// Автотесты
// =========================

async function runAllTests() {
    const statusDiv = document.getElementById('tests-status');
    const statusText = document.getElementById('tests-status-text');
    statusDiv.style.display = 'block';
    statusText.textContent = 'Запуск тестов...';

    try {
        const response = await fetch(`${API_URL}/tests/run`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                test_group: 'all',
                headed: false
            })
        });
        const data = await response.json();

        if (data.success) {
            statusText.textContent = 'Тесты выполнены успешно!';
            const progressDiv = document.getElementById('tests-progress');
            progressDiv.innerHTML = `
                <div style="padding: 10px; background: #e8f5e9; border-radius: 6px; color: #2e7d32; margin-top: 10px;">
                    <strong>✓ Все тесты пройдены успешно!</strong>
                </div>
            `;
            setTimeout(() => {
                statusDiv.style.display = 'none';
            }, 5000);
        } else {
            statusText.textContent = 'Тесты завершились с ошибками';
            const progressDiv = document.getElementById('tests-progress');
            progressDiv.innerHTML = `
                <div style="padding: 10px; background: #ffebee; border-radius: 6px; color: #c62828; margin-top: 10px;">
                    <strong>✗ Некоторые тесты провалились</strong><br>
                    <small>Откройте панель тестов для подробностей</small>
                </div>
            `;
        }
    } catch (error) {
        console.error('Ошибка запуска тестов:', error);
        statusText.textContent = 'Ошибка!';
        const progressDiv = document.getElementById('tests-progress');
        progressDiv.innerHTML = `
            <div style="padding: 10px; background: #ffebee; border-radius: 6px; color: #c62828; margin-top: 10px;">
                <strong>✗ Ошибка:</strong> ${error.message}
            </div>
        `;
    }
}

async function cleanupTestData() {
    if (!confirm('Вы уверены, что хотите удалить все тестовые данные? Это действие нельзя отменить.')) {
        return;
    }

    const statusDiv = document.getElementById('cleanup-status');
    statusDiv.style.display = 'block';
    statusDiv.innerHTML = '<div style="color: #ff9800;">⏳ Удаление тестовых данных...</div>';

    try {
        const response = await fetch(`${API_URL}/tests/cleanup`, {
            method: 'POST'
        });
        const data = await response.json();

        if (data.success) {
            statusDiv.innerHTML = `
                <div style="padding: 10px; background: #e8f5e9; border-radius: 6px; color: #2e7d32;">
                    <strong>✓ Тестовые данные удалены!</strong><br>
                    <small>Викторин: ${data.stats.quizzes}, Вопросов: ${data.stats.questions}, PDF: ${data.stats.pdfs}</small>
                </div>
            `;
            // Обновляем список вопросов
            if (currentTab === 'questions') {
                loadQuestions();
            }
            setTimeout(() => {
                statusDiv.style.display = 'none';
            }, 5000);
        } else {
            statusDiv.innerHTML = `
                <div style="padding: 10px; background: #ffebee; border-radius: 6px; color: #c62828;">
                    <strong>✗ Ошибка:</strong> ${data.error}
                </div>
            `;
        }
    } catch (error) {
        console.error('Ошибка очистки:', error);
        statusDiv.innerHTML = `
            <div style="padding: 10px; background: #ffebee; border-radius: 6px; color: #c62828;">
                <strong>✗ Ошибка:</strong> ${error.message}
            </div>
        `;
    }
}

async function loadAdminStats() {
    const container = document.getElementById('admin-stats-container');
    container.innerHTML = '<div class="loading">Загрузка статистики...</div>';

    try {
        const response = await fetch(`${API_URL}/stats`);
        const data = await response.json();

        if (data.success) {
            const stats = data.stats;
            container.innerHTML = `
                <div class="stats-grid">
                    <div class="stat-card" style="background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);">
                        <div class="stat-label">Всего вопросов</div>
                        <div class="stat-number">${stats.total_questions || 0}</div>
                    </div>
                    <div class="stat-card" style="background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%);">
                        <div class="stat-label">Предметов</div>
                        <div class="stat-number">${Object.keys(stats.by_subject || {}).length}</div>
                    </div>
                    <div class="stat-card" style="background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);">
                        <div class="stat-label">Университетов</div>
                        <div class="stat-number">${Object.keys(stats.by_university || {}).length}</div>
                    </div>
                </div>
            `;
        }
    } catch (error) {
        console.error('Ошибка загрузки статистики:', error);
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">⚠️</div>
                <h3>Ошибка загрузки статистики</h3>
                <p>${error.message}</p>
            </div>
        `;
    }
}

// =========================
// ЗАГРУЗЧИК ИЗ СЕТИ
// =========================

// Запустить загрузчик
async function startDownloader(mode) {
    const statusDiv = document.getElementById('downloader-status');
    const statusText = document.getElementById('downloader-status-text');
    const logsDiv = document.getElementById('downloader-logs');

    try {
        statusDiv.style.display = 'block';
        statusText.textContent = 'Запуск загрузчика...';
        statusText.style.color = '#ff9800';

        const response = await fetch(`${API_URL}/downloader/start`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ mode: mode })
        });

        const data = await response.json();

        if (data.success) {
            statusText.textContent = `Загрузчик запущен (${mode})`;
            statusText.style.color = '#4caf50';

            // Начинаем автообновление логов
            startLogsAutoRefresh();

            alert(`✅ Загрузчик запущен в режиме: ${mode}\n\nЛоги будут обновляться автоматически.`);
        } else {
            statusText.textContent = 'Ошибка запуска';
            statusText.style.color = '#f44336';
            alert('❌ Ошибка: ' + data.error);
        }
    } catch (error) {
        console.error('Ошибка запуска загрузчика:', error);
        statusText.textContent = 'Ошибка';
        statusText.style.color = '#f44336';
        alert('❌ Ошибка запуска загрузчика');
    }
}

// Автообновление логов
let logsRefreshInterval = null;

function startLogsAutoRefresh() {
    // Останавливаем предыдущий интервал
    if (logsRefreshInterval) {
        clearInterval(logsRefreshInterval);
    }

    // Обновляем логи каждые 3 секунды
    logsRefreshInterval = setInterval(refreshDownloaderLogs, 3000);

    // Первое обновление сразу
    refreshDownloaderLogs();
}

function stopLogsAutoRefresh() {
    if (logsRefreshInterval) {
        clearInterval(logsRefreshInterval);
        logsRefreshInterval = null;
    }
}

// Обновить логи загрузчика
async function refreshDownloaderLogs() {
    const logsDiv = document.getElementById('downloader-logs');

    try {
        const response = await fetch(`${API_URL}/downloader/logs`);
        const data = await response.json();

        if (data.success && data.logs) {
            if (data.logs.length === 0) {
                logsDiv.innerHTML = '<div style="color: #888;">Логи пока пустые...</div>';
            } else {
                // Форматируем логи с подсветкой
                const formattedLogs = data.logs.map(line => {
                    let color = '#d4d4d4';
                    if (line.includes('ERROR') || line.includes('Ошибка') || line.includes('✗')) {
                        color = '#f48771';
                    } else if (line.includes('WARNING') || line.includes('⚠')) {
                        color = '#dcdcaa';
                    } else if (line.includes('INFO') || line.includes('✓')) {
                        color = '#4ec9b0';
                    } else if (line.includes('СТАРТ') || line.includes('ГОТОВО') || line.includes('ИТОГИ')) {
                        color = '#569cd6';
                    }
                    return `<div style="color: ${color};">${line}</div>`;
                }).join('');

                logsDiv.innerHTML = formattedLogs;
                // Прокручиваем вниз
                logsDiv.scrollTop = logsDiv.scrollHeight;
            }
        }
    } catch (error) {
        console.error('Ошибка загрузки логов:', error);
    }
}

// Загрузить статистику загрузчика
async function loadDownloaderStats() {
    const container = document.getElementById('downloader-stats');
    container.innerHTML = '<div style="color: #999; padding: 20px; text-align: center;">Загрузка...</div>';

    try {
        const response = await fetch(`${API_URL}/downloader/stats`);
        const data = await response.json();

        if (data.success && data.stats) {
            const stats = data.stats;
            const totalFiles = stats.total_files || 0;
            const lastUpdate = stats.last_update
                ? new Date(stats.last_update).toLocaleString('ru-RU')
                : 'Никогда';

            let statsHtml = `
                <div style="text-align: center; margin-bottom: 15px;">
                    <div style="font-size: 2.5em; font-weight: bold; color: #667eea;">${totalFiles}</div>
                    <div style="color: #666; margin-top: 5px;">Всего файлов</div>
                </div>
                <div style="text-align: center; margin-bottom: 15px; padding: 10px; background: #f9f9f9; border-radius: 5px;">
                    <div style="font-size: 0.85em; color: #666;">Последнее обновление:</div>
                    <div style="font-weight: 600; margin-top: 5px;">${lastUpdate}</div>
                </div>
            `;

            // Топ источников
            if (stats.by_source && Object.keys(stats.by_source).length > 0) {
                statsHtml += '<div style="margin-top: 15px;"><div style="font-weight: 600; margin-bottom: 10px;">📊 По источникам:</div>';
                const sorted = Object.entries(stats.by_source).sort((a, b) => b[1] - a[1]).slice(0, 5);
                sorted.forEach(([source, count]) => {
                    statsHtml += `
                        <div style="display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid #eee;">
                            <span style="font-size: 0.85em;">${source}</span>
                            <span style="font-weight: 600; color: #667eea;">${count}</span>
                        </div>
                    `;
                });
                statsHtml += '</div>';
            }

            container.innerHTML = statsHtml;
        } else {
            container.innerHTML = '<div style="color: #999; text-align: center;">Нет данных</div>';
        }
    } catch (error) {
        console.error('Ошибка загрузки статистики:', error);
        container.innerHTML = '<div style="color: #f44336; text-align: center;">Ошибка загрузки</div>';
    }
}

// Загрузить список источников
async function loadSourcesList() {
    const container = document.getElementById('sources-list');
    container.innerHTML = '<div style="padding: 20px; text-align: center; color: #999;">Загрузка источников...</div>';

    try {
        const response = await fetch(`${API_URL}/downloader/sources`);
        const data = await response.json();

        if (data.success && data.sources) {
            const sources = data.sources;

            if (Object.keys(sources).length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">📭</div>
                        <h3>Нет источников</h3>
                        <p>Добавьте первый источник для загрузки материалов</p>
                    </div>
                `;
                return;
            }

            let html = '<div style="display: flex; flex-direction: column; gap: 10px;">';

            for (const [name, config] of Object.entries(sources)) {
                const urlCount = config.urls ? config.urls.length : 0;
                const type = config.type || 'requests';

                html += `
                    <div style="border: 2px solid #e0e0e0; padding: 15px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center;">
                        <div style="flex: 1;">
                            <div style="font-weight: 600; font-size: 1.1em; margin-bottom: 5px;">${name}</div>
                            <div style="color: #666; font-size: 0.9em;">
                                📌 ${urlCount} URL(s) |
                                ${type === 'selenium' ? '🌐 Selenium (JavaScript)' : '🔗 Requests'}
                            </div>
                            <div style="margin-top: 8px; max-height: 100px; overflow-y: auto;">
                                ${config.urls.slice(0, 3).map(url =>
                                    `<div style="font-size: 0.8em; color: #999; margin-top: 3px;">• ${url}</div>`
                                ).join('')}
                                ${urlCount > 3 ? `<div style="font-size: 0.8em; color: #999; margin-top: 3px;">... и еще ${urlCount - 3}</div>` : ''}
                            </div>
                        </div>
                        <div style="display: flex; gap: 10px;">
                            <button onclick="editSource('${name}')" class="btn-secondary" style="padding: 8px 15px; font-size: 0.9em;">
                                ✏️ Изменить
                            </button>
                            <button onclick="deleteSource('${name}')" class="btn-danger" style="padding: 8px 15px; font-size: 0.9em;">
                                🗑️
                            </button>
                        </div>
                    </div>
                `;
            }

            html += '</div>';
            container.innerHTML = html;
        }
    } catch (error) {
        console.error('Ошибка загрузки источников:', error);
        container.innerHTML = '<div style="color: #f44336; padding: 20px; text-align: center;">Ошибка загрузки источников</div>';
    }
}

// Показать модальное окно добавления источника
function showAddSourceModal() {
    const modal = document.getElementById('edit-modal');

    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2>➕ Добавить источник загрузки</h2>
                <button class="close-btn" onclick="closeEditModal()">✕</button>
            </div>
            <div class="modal-body">
                <form id="add-source-form">
                    <div class="form-group">
                        <label>Название источника:</label>
                        <input type="text" id="source-name" placeholder="МГУ_Ломоносов" required>
                        <small style="color: #666;">Используйте латиницу и подчеркивания</small>
                    </div>

                    <div class="form-group">
                        <label>Тип загрузчика:</label>
                        <select id="source-type">
                            <option value="requests">Requests (простые HTML страницы)</option>
                            <option value="selenium">Selenium (сайты с JavaScript)</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label>URL адреса (по одному на строку):</label>
                        <textarea id="source-urls" rows="8" placeholder="https://example.com/page1&#10;https://example.com/page2" required></textarea>
                        <small style="color: #666;">Каждый URL с новой строки</small>
                    </div>

                    <div class="form-actions">
                        <button type="button" onclick="saveNewSource()" class="btn-primary">💾 Сохранить источник</button>
                        <button type="button" onclick="closeEditModal()" class="btn-secondary">Отмена</button>
                    </div>
                </form>
            </div>
        </div>
    `;

    modal.style.display = 'flex';
}

// Сохранить новый источник
async function saveNewSource() {
    const name = document.getElementById('source-name').value.trim();
    const type = document.getElementById('source-type').value;
    const urlsText = document.getElementById('source-urls').value.trim();

    if (!name || !urlsText) {
        alert('❌ Заполните все обязательные поля');
        return;
    }

    // Разбиваем URL на массив
    const urls = urlsText.split('\n')
        .map(url => url.trim())
        .filter(url => url.length > 0);

    if (urls.length === 0) {
        alert('❌ Добавьте хотя бы один URL');
        return;
    }

    try {
        const response = await fetch(`${API_URL}/downloader/sources`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: name,
                config: {
                    urls: urls,
                    type: type
                }
            })
        });

        const data = await response.json();

        if (data.success) {
            alert('✅ Источник успешно добавлен!');
            closeEditModal();
            loadSourcesList();
        } else {
            alert('❌ Ошибка: ' + data.error);
        }
    } catch (error) {
        console.error('Ошибка сохранения источника:', error);
        alert('❌ Ошибка сохранения источника');
    }
}

// Редактировать источник
async function editSource(name) {
    try {
        const response = await fetch(`${API_URL}/downloader/sources`);
        const data = await response.json();

        if (data.success && data.sources[name]) {
            const config = data.sources[name];
            const modal = document.getElementById('edit-modal');

            modal.innerHTML = `
                <div class="modal-content">
                    <div class="modal-header">
                        <h2>✏️ Редактировать источник: ${name}</h2>
                        <button class="close-btn" onclick="closeEditModal()">✕</button>
                    </div>
                    <div class="modal-body">
                        <form id="edit-source-form">
                            <div class="form-group">
                                <label>Название источника:</label>
                                <input type="text" id="edit-source-name" value="${name}" disabled>
                                <small style="color: #666;">Название нельзя изменить</small>
                            </div>

                            <div class="form-group">
                                <label>Тип загрузчика:</label>
                                <select id="edit-source-type">
                                    <option value="requests" ${config.type === 'requests' ? 'selected' : ''}>Requests (простые HTML страницы)</option>
                                    <option value="selenium" ${config.type === 'selenium' ? 'selected' : ''}>Selenium (сайты с JavaScript)</option>
                                </select>
                            </div>

                            <div class="form-group">
                                <label>URL адреса (по одному на строку):</label>
                                <textarea id="edit-source-urls" rows="10">${config.urls.join('\n')}</textarea>
                            </div>

                            <div class="form-actions">
                                <button type="button" onclick="updateSource('${name}')" class="btn-primary">💾 Сохранить изменения</button>
                                <button type="button" onclick="closeEditModal()" class="btn-secondary">Отмена</button>
                            </div>
                        </form>
                    </div>
                </div>
            `;

            modal.style.display = 'flex';
        }
    } catch (error) {
        console.error('Ошибка загрузки источника:', error);
        alert('❌ Ошибка загрузки данных источника');
    }
}

// Обновить источник
async function updateSource(name) {
    const type = document.getElementById('edit-source-type').value;
    const urlsText = document.getElementById('edit-source-urls').value.trim();

    const urls = urlsText.split('\n')
        .map(url => url.trim())
        .filter(url => url.length > 0);

    if (urls.length === 0) {
        alert('❌ Добавьте хотя бы один URL');
        return;
    }

    try {
        const response = await fetch(`${API_URL}/downloader/sources/${encodeURIComponent(name)}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                urls: urls,
                type: type
            })
        });

        const data = await response.json();

        if (data.success) {
            alert('✅ Источник успешно обновлён!');
            closeEditModal();
            loadSourcesList();
        } else {
            alert('❌ Ошибка: ' + data.error);
        }
    } catch (error) {
        console.error('Ошибка обновления источника:', error);
        alert('❌ Ошибка обновления источника');
    }
}

// Удалить источник
async function deleteSource(name) {
    if (!confirm(`❌ Вы уверены, что хотите удалить источник "${name}"?\n\nЭто действие нельзя отменить!`)) {
        return;
    }

    try {
        const response = await fetch(`${API_URL}/downloader/sources/${encodeURIComponent(name)}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            alert('✅ Источник успешно удалён!');
            loadSourcesList();
        } else {
            alert('❌ Ошибка: ' + data.error);
        }
    } catch (error) {
        console.error('Ошибка удаления источника:', error);
        alert('❌ Ошибка удаления источника');
    }
}

// =========================
// УПРАВЛЕНИЕ ПРЕДМЕТАМИ
// =========================

// Загрузить список предметов
async function loadSubjectsList() {
    const container = document.getElementById('subjects-list');
    container.innerHTML = '<div style="padding: 20px; text-align: center; color: #999;">Загрузка предметов...</div>';

    try {
        const response = await fetch(`${API_URL}/downloader/subjects`);
        const data = await response.json();

        if (data.success && data.subjects) {
            const subjects = data.subjects;

            if (subjects.length === 0) {
                container.innerHTML = '<div style="color: #999; padding: 10px;">Нет предметов для поиска</div>';
                return;
            }

            let html = '';
            subjects.forEach(subject => {
                html += `
                    <div style="display: inline-flex; align-items: center; gap: 8px; padding: 8px 12px; background: #e3f2fd; border-radius: 20px; border: 2px solid #2196f3;">
                        <span style="font-weight: 500;">${subject}</span>
                        <button onclick="deleteSubject('${subject}')" style="background: none; border: none; cursor: pointer; color: #f44336; font-size: 1.2em; padding: 0; line-height: 1;" title="Удалить">
                            ✕
                        </button>
                    </div>
                `;
            });

            container.innerHTML = html;
        }
    } catch (error) {
        console.error('Ошибка загрузки предметов:', error);
        container.innerHTML = '<div style="color: #f44336; padding: 10px;">Ошибка загрузки предметов</div>';
    }
}

// Показать модальное окно добавления предмета
function showAddSubjectModal() {
    const modal = document.getElementById('edit-modal');

    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2>➕ Добавить предмет для поиска</h2>
                <button class="close-btn" onclick="closeEditModal()">✕</button>
            </div>
            <div class="modal-body">
                <form id="add-subject-form">
                    <div class="form-group">
                        <label>Название предмета:</label>
                        <input type="text" id="subject-name" placeholder="философия" required>
                        <small style="color: #666;">Название должно быть в нижнем регистре, например: "философия", "обществознание"</small>
                    </div>

                    <div class="form-group">
                        <label>Примеры предметов:</label>
                        <div style="background: #f9f9f9; padding: 10px; border-radius: 5px; font-size: 0.9em; color: #666;">
                            <div>• религиоведение</div>
                            <div>• обществознание</div>
                            <div>• философия</div>
                            <div>• право</div>
                            <div>• политология</div>
                            <div>• социология</div>
                            <div>• экономика</div>
                            <div>• история</div>
                            <div>• журналистика</div>
                            <div>• иностранный язык</div>
                        </div>
                    </div>

                    <div class="form-actions">
                        <button type="button" onclick="addSubject()" class="btn-primary">💾 Добавить предмет</button>
                        <button type="button" onclick="closeEditModal()" class="btn-secondary">Отмена</button>
                    </div>
                </form>
            </div>
        </div>
    `;

    modal.style.display = 'flex';
}

// Добавить предмет
async function addSubject() {
    const name = document.getElementById('subject-name').value.trim().toLowerCase();

    if (!name) {
        alert('❌ Введите название предмета');
        return;
    }

    try {
        const response = await fetch(`${API_URL}/downloader/subjects`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ subject: name })
        });

        const data = await response.json();

        if (data.success) {
            alert('✅ Предмет успешно добавлен!');
            closeEditModal();
            loadSubjectsList();
        } else {
            alert('❌ Ошибка: ' + data.error);
        }
    } catch (error) {
        console.error('Ошибка добавления предмета:', error);
        alert('❌ Ошибка добавления предмета');
    }
}

// Удалить предмет
async function deleteSubject(subject) {
    if (!confirm(`❌ Вы уверены, что хотите удалить предмет "${subject}"?\n\nЗагрузчик больше не будет искать материалы по этому предмету.`)) {
        return;
    }

    try {
        const response = await fetch(`${API_URL}/downloader/subjects/${encodeURIComponent(subject)}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            alert('✅ Предмет успешно удалён!');
            loadSubjectsList();
        } else {
            alert('❌ Ошибка: ' + data.error);
        }
    } catch (error) {
        console.error('Ошибка удаления предмета:', error);
        alert('❌ Ошибка удаления предмета');
    }
}

// =========================
// Запуск при загрузке
// =========================

window.addEventListener('DOMContentLoaded', init);