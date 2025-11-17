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
    } else if (tabName === 'pdfs') {
        loadPDFList();
    } else if (tabName === 'admin') {
        loadAdminStats();
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
    const container = document.getElementById('pdf-list-container');
    container.innerHTML = '<div class="loading">Загрузка списка PDF...</div>';

    try {
        const params = new URLSearchParams();

        const university = document.getElementById('pdf-filter-university')?.value;
        const subject = document.getElementById('pdf-filter-subject')?.value;
        const year = document.getElementById('pdf-filter-year')?.value;
        const search = document.getElementById('pdf-search')?.value;

        if (university) params.append('university', university);
        if (subject) params.append('subject', subject);
        if (year) params.append('year', year);
        if (search) params.append('search', search);

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
                            <button onclick="reparsePDF(${pdf.id})" class="edit-btn" style="background: #2196f3;">
                                🔄 Перепарсить
                            </button>
                            <button onclick="viewPDFQuestions(${pdf.id})" class="edit-btn" style="background: #ff9800;">
                                📝 Вопросы
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
                    <button class="close-btn" onclick="closeEditModal()">&times;</button>
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

                        <label class="checkbox-label">
                            <input type="checkbox" id="edit-cascade" checked>
                            Обновить теги у всех вопросов из этого PDF
                        </label>

                        <div class="form-actions">
                            <button type="submit" class="btn-primary">💾 Сохранить изменения</button>
                            <button type="button" class="btn-secondary" onclick="closeEditModal()">Отмена</button>
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

function closeEditModal() {
    const modal = document.getElementById('edit-modal');
    modal.style.display = 'none';
    modal.innerHTML = '';
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

        // Создаем модальное окно с вопросами
        const modal = document.getElementById('edit-modal');
        modal.style.display = 'flex';
        modal.innerHTML = `
            <div class="modal-content" style="max-width: 1000px;">
                <div class="modal-header">
                    <h2>Вопросы из: ${pdf.display_name}</h2>
                    <button class="close-btn" onclick="closeEditModal()">&times;</button>
                </div>
                <div class="modal-body">
                    <p><strong>Всего вопросов:</strong> ${questionsData.count}</p>
                    <div style="max-height: 500px; overflow-y: auto; margin-top: 20px;">
                        ${questionsData.questions.slice(0, 20).map((q, idx) => `
                            <div class="question-card" style="margin-bottom: 15px;">
                                <div class="question-text">
                                    <strong>${idx + 1}.</strong> ${q.text.substring(0, 200)}${q.text.length > 200 ? '...' : ''}
                                </div>
                                <div class="question-meta" style="margin-top: 10px;">
                                    <span class="tag">${getTypeLabel(q.type)}</span>
                                    ${q.verified ? '<span class="tag correct">✓ Проверено</span>' : '<span class="tag incorrect">✗ Не проверено</span>'}
                                </div>
                            </div>
                        `).join('')}
                        ${questionsData.count > 20 ? `<p style="text-align: center; color: #666;">... и еще ${questionsData.count - 20} вопросов</p>` : ''}
                    </div>
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Ошибка просмотра вопросов:', error);
        alert('Ошибка: ' + error.message);
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
// Запуск при загрузке
// =========================

window.addEventListener('DOMContentLoaded', init);