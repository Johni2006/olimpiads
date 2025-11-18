// Функции для редактирования вопросов

// Конфигурация API (должна совпадать с app.js)
const API_URL = 'http://localhost:5001/api';

let currentEditingQuestion = null;

// Показать модальное окно редактирования
function showEditModal(questionId) {
    // Загружаем вопрос
    fetch(`${API_URL}/questions/${questionId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                currentEditingQuestion = data.question;
                renderEditForm(data.question);
                document.getElementById('edit-modal').style.display = 'flex';
            }
        })
        .catch(error => {
            console.error('Ошибка загрузки вопроса:', error);
            alert('Ошибка загрузки вопроса');
        });
}

// Закрыть модальное окно
function closeEditModal() {
    document.getElementById('edit-modal').style.display = 'none';
    currentEditingQuestion = null;
}

// Отрисовать форму редактирования
function renderEditForm(question) {
    const modal = document.getElementById('edit-modal');
    const tags = question.tags || {};

    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2>✏️ Редактирование вопроса #${question.id}</h2>
                <div style="display: flex; gap: 10px; align-items: center;">
                    ${question.source_pdf ? `
                        <a href="${API_URL}/pdf/${encodeURIComponent(question.source_pdf)}"
                           target="_blank"
                           class="view-pdf-btn"
                           title="Посмотреть исходный PDF">
                            📄 PDF
                        </a>
                    ` : ''}
                    <button class="close-btn" onclick="closeEditModal()">✕</button>
                </div>
            </div>

            <div class="modal-body">
                <form id="edit-form">
                    <!-- Текст вопроса -->
                    <div class="form-group">
                        <label>Текст вопроса:</label>
                        <textarea id="edit-text" rows="4">${question.text}</textarea>
                    </div>

                    <!-- Тип вопроса -->
                    <div class="form-group">
                        <label>Тип вопроса:</label>
                        <select id="edit-type" onchange="updateQuestionTypeFields()">
                            <option value="choice" ${question.type === 'choice' ? 'selected' : ''}>Одиночный выбор</option>
                            <option value="multiple_choice" ${question.type === 'multiple_choice' ? 'selected' : ''}>Множественный выбор</option>
                            <option value="matching" ${question.type === 'matching' ? 'selected' : ''}>Соответствие</option>
                            <option value="text" ${question.type === 'text' ? 'selected' : ''}>Текстовый ответ</option>
                            <option value="essay" ${question.type === 'essay' ? 'selected' : ''}>Эссе</option>
                        </select>
                    </div>

                    <!-- Сложность и баллы -->
                    <div class="form-row">
                        <div class="form-group">
                            <label>Сложность (1-5):</label>
                            <input type="number" id="edit-difficulty" min="1" max="5" value="${question.difficulty || 1}">
                        </div>
                        <div class="form-group">
                            <label>Баллы:</label>
                            <input type="number" id="edit-points" step="0.5" value="${question.points || 1}">
                        </div>
                    </div>

                    <!-- Предмет и Университет -->
                    <div class="form-row">
                        <div class="form-group">
                            <label>Предмет:</label>
                            <input type="text" id="edit-subject" value="${(tags.subject || [])[0] || ''}">
                        </div>
                        <div class="form-group">
                            <label>Университет:</label>
                            <input type="text" id="edit-university" value="${(tags.university || [])[0] || ''}">
                        </div>
                    </div>

                    <!-- Год -->
                    <div class="form-group">
                        <label>Год:</label>
                        <input type="text" id="edit-year" value="${(tags.year || [])[0] || ''}">
                    </div>

                    <!-- Варианты ответов (только для choice/multiple_choice) -->
                    <div id="options-container" style="display: ${question.type.includes('choice') ? 'block' : 'none'}">
                        <label>Варианты ответов:</label>
                        <div id="edit-options">
                            ${(question.options || []).map((opt, i) => `
                                <div class="option-edit">
                                    <input type="checkbox"
                                           id="opt-correct-${i}"
                                           ${opt.is_correct ? 'checked' : ''}>
                                    <input type="text"
                                           id="opt-text-${i}"
                                           value="${opt.text}"
                                           placeholder="Вариант ${i + 1}">
                                    <button type="button" onclick="removeOption(${i})">✕</button>
                                </div>
                            `).join('')}
                        </div>
                        <button type="button" onclick="addOption()" class="btn-secondary">+ Добавить вариант</button>
                    </div>

                    <!-- Рекомендации для эссе -->
                    <div id="essay-container" style="display: ${question.type === 'essay' ? 'block' : 'none'}">
                        <div class="form-group">
                            <label>Рекомендации по оцениванию:</label>
                            <textarea id="essay-guidelines" rows="8" placeholder="Опишите критерии оценивания, ключевые моменты, которые должны быть раскрыты...">${(question.options && question.options[0]) ? question.options[0].text : ''}</textarea>
                        </div>
                    </div>

                    <!-- Проверено -->
                    <div class="form-group">
                        <label class="checkbox-label">
                            <input type="checkbox" id="edit-verified" ${question.verified ? 'checked' : ''}>
                            ✓ Вопрос проверен вручную
                        </label>
                    </div>

                    <!-- Кнопки -->
                    <div class="form-actions">
                        <button type="button" onclick="saveQuestion()" class="btn-primary">💾 Сохранить</button>
                        <button type="button" onclick="closeEditModal()" class="btn-secondary">Отмена</button>
                        <button type="button" onclick="deleteQuestion(${question.id})" class="btn-danger" style="margin-left: auto;">🗑️ Удалить вопрос</button>
                    </div>
                </form>
            </div>
        </div>
    `;
}

// Добавить вариант ответа
function addOption() {
    const container = document.getElementById('edit-options');
    const count = container.children.length;

    const optionDiv = document.createElement('div');
    optionDiv.className = 'option-edit';
    optionDiv.innerHTML = `
        <input type="checkbox" id="opt-correct-${count}">
        <input type="text" id="opt-text-${count}" placeholder="Вариант ${count + 1}">
        <button type="button" onclick="removeOption(${count})">✕</button>
    `;

    container.appendChild(optionDiv);
}

// Удалить вариант ответа
function removeOption(index) {
    const option = document.getElementById(`opt-text-${index}`).parentElement;
    option.remove();
}

// Сохранить изменения
async function saveQuestion() {
    if (!currentEditingQuestion) return;

    const questionId = currentEditingQuestion.id;

    // Собираем данные из формы
    const data = {
        text: document.getElementById('edit-text').value,
        type: document.getElementById('edit-type').value,
        difficulty: parseInt(document.getElementById('edit-difficulty').value),
        points: parseFloat(document.getElementById('edit-points').value),
        verified: document.getElementById('edit-verified').checked,
        tags: {
            subject: [document.getElementById('edit-subject').value].filter(v => v),
            university: [document.getElementById('edit-university').value].filter(v => v),
            year: [document.getElementById('edit-year').value].filter(v => v)
        },
        options: []
    };

    // Собираем варианты ответов
    const optionsContainer = document.getElementById('edit-options');
    if (optionsContainer && (data.type === 'choice' || data.type === 'multiple_choice')) {
        const optionDivs = optionsContainer.querySelectorAll('.option-edit');
        optionDivs.forEach((div, i) => {
            const textInput = div.querySelector(`#opt-text-${i}`);
            const correctCheckbox = div.querySelector(`#opt-correct-${i}`);

            if (textInput && textInput.value.trim()) {
                data.options.push({
                    text: textInput.value.trim(),
                    is_correct: correctCheckbox ? correctCheckbox.checked : false
                });
            }
        });
    }

    // Для эссе сохраняем рекомендации как первый вариант ответа
    if (data.type === 'essay') {
        const guidelines = document.getElementById('essay-guidelines');
        if (guidelines && guidelines.value.trim()) {
            data.options.push({
                text: guidelines.value.trim(),
                is_correct: false // Для эссе нет правильного ответа
            });
        }
    }

    try {
        const response = await fetch(`${API_URL}/questions/${questionId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            alert('✅ Вопрос успешно обновлён!');
            closeEditModal();

            // Если редактируем из просмотра PDF - обновляем список вопросов PDF
            if (typeof refreshPDFQuestions === 'function' && window.currentPdfId) {
                await refreshPDFQuestions();
            } else {
                // Иначе перезагружаем список вопросов на странице "Просмотр вопросов"
                applyFilters();
            }
        } else {
            alert('❌ Ошибка: ' + result.error);
        }
    } catch (error) {
        console.error('Ошибка сохранения:', error);
        alert('❌ Ошибка сохранения');
    }
}

// Удалить вопрос
async function deleteQuestion(questionId) {
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
            closeEditModal();

            // Обновляем список вопросов
            if (typeof refreshPDFQuestions === 'function' && window.currentPdfId) {
                await refreshPDFQuestions();
            } else if (typeof applyFilters === 'function') {
                applyFilters();
            }
        } else {
            alert('❌ Ошибка: ' + result.error);
        }
    } catch (error) {
        console.error('Ошибка удаления:', error);
        alert('❌ Ошибка удаления вопроса');
    }
}

// Обновить поля формы при изменении типа вопроса
function updateQuestionTypeFields() {
    const type = document.getElementById('edit-type').value;
    const optionsContainer = document.getElementById('options-container');
    const essayContainer = document.getElementById('essay-container');

    // Показываем варианты ответов только для choice и multiple_choice
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
