// Функции для редактирования вопросов

// Используем API_URL из app.js (уже объявлена там)
// const API_URL = 'http://localhost:5001/api'; - закомментировано, чтобы избежать конфликта

let currentEditingQuestion = null;

// Показать модальное окно редактирования
window.showEditModal = function showEditModal(questionId) {
    // Загружаем вопрос
    fetch(`${API_URL}/questions/${questionId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                currentEditingQuestion = data.question;
                renderEditForm(data.question);
                document.getElementById('edit-modal').style.display = 'flex';

                // Загружаем изображения вопроса
                setTimeout(() => {
                    loadQuestionImages(data.question.id);
                }, 100);

                // Загружаем изображения для вариантов ответа
                if (data.question.options && data.question.options.length > 0) {
                    setTimeout(() => {
                        loadOptionImages(data.question.options);
                    }, 100);
                }

                // Загружаем изображения для пар соответствия
                if (data.question.matching_pairs && data.question.matching_pairs.length > 0) {
                    setTimeout(() => {
                        loadMatchingImages(data.question.matching_pairs);
                    }, 100);
                }
            }
        })
        .catch(error => {
            console.error('Ошибка загрузки вопроса:', error);
            alert('Ошибка загрузки вопроса');
        });
}

// Закрыть модальное окно
window.closeEditModal = function closeEditModal() {
    const modal = document.getElementById('edit-modal');
    if (modal) {
        modal.style.display = 'none';
        // Очищаем содержимое для освобождения памяти
        setTimeout(() => {
            modal.innerHTML = '';
        }, 300); // Небольшая задержка для анимации закрытия
    }
    currentEditingQuestion = null;
}

// Отрисовать форму редактирования
window.renderEditForm = function renderEditForm(question) {
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

                    <!-- Изображения к вопросу -->
                    <div class="form-group">
                        <label>Изображения к вопросу:</label>
                        <div id="question-images" class="question-images"></div>
                        <button type="button" onclick="uploadQuestionImage()" class="btn-image" style="margin-top: 10px;">
                            🖼️ Загрузить изображение
                        </button>
                        <small style="display: block; margin-top: 5px; color: #888;">
                            Изображения будут отображаться над текстом вопроса
                        </small>
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
                                <div class="option-edit" data-option-id="${opt.id || ''}">
                                    <input type="checkbox"
                                           id="opt-correct-${i}"
                                           onchange="handleCorrectCheckbox(${i})"
                                           ${opt.is_correct ? 'checked' : ''}>
                                    <input type="text"
                                           id="opt-text-${i}"
                                           value="${opt.text}"
                                           placeholder="Вариант ${i + 1}">
                                    ${opt.id ? `
                                        <button type="button" onclick="uploadOptionImage(${opt.id}, ${i})" class="btn-image" title="Загрузить изображение">🖼️</button>
                                    ` : `
                                        <span class="save-first-hint" title="Сначала сохраните вопрос, чтобы добавить изображение">💾</span>
                                    `}
                                    <button type="button" onclick="removeOption(${i})">✕</button>
                                    <div id="opt-images-${i}" class="option-images"></div>
                                </div>
                            `).join('')}
                        </div>
                        <button type="button" onclick="addOption()" class="btn-secondary">+ Добавить вариант</button>
                    </div>

                    <!-- Пары соответствия (только для matching) -->
                    <div id="matching-container" style="display: ${question.type === 'matching' ? 'block' : 'none'}">
                        <label>Пары соответствия:</label>
                        <div id="edit-matching">
                            ${(question.matching_pairs || []).map((pair, i) => `
                                <div class="matching-pair-edit" data-pair-id="${pair.id || ''}">
                                    <div class="matching-pair-inputs">
                                        <div class="matching-side">
                                            <input type="text"
                                                   id="pair-left-${i}"
                                                   value="${pair.left_text}"
                                                   placeholder="Левая часть ${i + 1}">
                                            ${pair.id ? `
                                                <button type="button" onclick="uploadMatchingImage(${pair.id}, ${i}, 'left')" class="btn-image" title="Загрузить изображение для левой части">🖼️ L</button>
                                            ` : `
                                                <span class="save-first-hint" title="Сначала сохраните вопрос">💾</span>
                                            `}
                                            <div id="pair-left-images-${i}" class="matching-images"></div>
                                        </div>
                                        <span class="matching-arrow">↔</span>
                                        <div class="matching-side">
                                            <input type="text"
                                                   id="pair-right-${i}"
                                                   value="${pair.right_text}"
                                                   placeholder="Правая часть ${i + 1}">
                                            ${pair.id ? `
                                                <button type="button" onclick="uploadMatchingImage(${pair.id}, ${i}, 'right')" class="btn-image" title="Загрузить изображение для правой части">🖼️ R</button>
                                            ` : `
                                                <span class="save-first-hint" title="Сначала сохраните вопрос">💾</span>
                                            `}
                                            <div id="pair-right-images-${i}" class="matching-images"></div>
                                        </div>
                                    </div>
                                    <button type="button" onclick="removeMatchingPair(${i})" class="btn-remove-pair">✕</button>
                                </div>
                            `).join('')}
                        </div>
                        <button type="button" onclick="addMatchingPair()" class="btn-secondary">+ Добавить пару</button>
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
window.addOption = function addOption() {
    const container = document.getElementById('edit-options');
    const count = container.children.length;

    const optionDiv = document.createElement('div');
    optionDiv.className = 'option-edit';
    optionDiv.innerHTML = `
        <input type="checkbox" id="opt-correct-${count}" onchange="handleCorrectCheckbox(${count})">
        <input type="text" id="opt-text-${count}" placeholder="Вариант ${count + 1}">
        <button type="button" onclick="removeOption(${count})">✕</button>
    `;

    container.appendChild(optionDiv);
}

// Обработчик чекбокса правильного ответа
window.handleCorrectCheckbox = function handleCorrectCheckbox(index) {
    const questionType = document.getElementById('edit-type').value;

    // Для одиночного выбора снимаем галочки с остальных вариантов
    if (questionType === 'choice') {
        const checkbox = document.getElementById(`opt-correct-${index}`);
        if (checkbox && checkbox.checked) {
            // Снимаем галочки со всех остальных вариантов
            const container = document.getElementById('edit-options');
            const allCheckboxes = container.querySelectorAll('input[type="checkbox"]');
            allCheckboxes.forEach((cb, i) => {
                if (i !== index) {
                    cb.checked = false;
                }
            });
        }
    }
}

// Удалить вариант ответа
window.removeOption = function removeOption(index) {
    const option = document.getElementById(`opt-text-${index}`).parentElement;
    option.remove();
}

// Добавить пару соответствия
window.addMatchingPair = function addMatchingPair() {
    const container = document.getElementById('edit-matching');
    const count = container.children.length;

    const pairDiv = document.createElement('div');
    pairDiv.className = 'matching-pair-edit';
    pairDiv.innerHTML = `
        <input type="text" id="pair-left-${count}" placeholder="Левая часть ${count + 1}">
        <span class="matching-arrow">↔</span>
        <input type="text" id="pair-right-${count}" placeholder="Правая часть ${count + 1}">
        <button type="button" onclick="removeMatchingPair(${count})">✕</button>
    `;

    container.appendChild(pairDiv);
}

// Удалить пару соответствия
window.removeMatchingPair = function removeMatchingPair(index) {
    const pair = document.getElementById(`pair-left-${index}`).parentElement;
    pair.remove();
}

// Сохранить изменения
window.saveQuestion = async function saveQuestion() {
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

    // Собираем пары соответствия
    data.matching_pairs = [];
    const matchingContainer = document.getElementById('edit-matching');
    if (matchingContainer && data.type === 'matching') {
        const pairDivs = matchingContainer.querySelectorAll('.matching-pair-edit');
        pairDivs.forEach((div, i) => {
            const leftInput = div.querySelector(`#pair-left-${i}`);
            const rightInput = div.querySelector(`#pair-right-${i}`);

            if (leftInput && rightInput && leftInput.value.trim() && rightInput.value.trim()) {
                data.matching_pairs.push({
                    left_text: leftInput.value.trim(),
                    right_text: rightInput.value.trim()
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

    // ВАЛИДАЦИЯ: проверяем наличие вариантов ответа для типов choice/multiple_choice
    if ((data.type === 'choice' || data.type === 'multiple_choice') && data.options.length === 0) {
        alert('⚠️ Вопрос типа "Одиночный выбор" или "Множественный выбор" должен иметь хотя бы один вариант ответа!');
        return;
    }

    // ВАЛИДАЦИЯ: проверяем наличие пар для типа matching
    if (data.type === 'matching' && data.matching_pairs.length === 0) {
        alert('⚠️ Вопрос типа "Соответствие" должен иметь хотя бы одну пару соответствия!');
        return;
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
        alert('❌ Ошибка сохранения: ' + error.message);
    }
}

// Удалить вопрос
window.deleteQuestion = async function deleteQuestion(questionId) {
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
window.updateQuestionTypeFields = function updateQuestionTypeFields() {
    const type = document.getElementById('edit-type').value;
    const optionsContainer = document.getElementById('options-container');
    const matchingContainer = document.getElementById('matching-container');
    const essayContainer = document.getElementById('essay-container');

    // Показываем варианты ответов только для choice и multiple_choice
    if (type === 'choice' || type === 'multiple_choice') {
        optionsContainer.style.display = 'block';
        matchingContainer.style.display = 'none';
        essayContainer.style.display = 'none';
    } else if (type === 'matching') {
        optionsContainer.style.display = 'none';
        matchingContainer.style.display = 'block';
        essayContainer.style.display = 'none';
    } else if (type === 'essay') {
        optionsContainer.style.display = 'none';
        matchingContainer.style.display = 'none';
        essayContainer.style.display = 'block';
    } else {
        optionsContainer.style.display = 'none';
        matchingContainer.style.display = 'none';
        essayContainer.style.display = 'none';
    }
}

// Загрузить изображение для варианта ответа
window.uploadOptionImage = function uploadOptionImage(optionId, optionIndex) {
    // Создаем input для выбора файла
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/png,image/jpeg,image/jpg,image/gif,image/webp,image/svg+xml';

    input.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        // Проверяем размер файла (макс 5MB)
        if (file.size > 5 * 1024 * 1024) {
            alert('❌ Файл слишком большой. Максимальный размер: 5 МБ');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);
        formData.append('option_id', optionId);
        formData.append('question_id', currentEditingQuestion.id);
        formData.append('image_type', 'option');

        try {
            const response = await fetch(`${API_URL}/images/upload`, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                // Добавляем изображение в UI
                displayOptionImage(optionIndex, result);
                alert('✅ Изображение успешно загружено!');
            } else {
                alert('❌ Ошибка: ' + result.error);
            }
        } catch (error) {
            console.error('Ошибка загрузки изображения:', error);
            alert('❌ Ошибка загрузки изображения');
        }
    };

    input.click();
}

// Отобразить изображение варианта ответа
window.displayOptionImage = function displayOptionImage(optionIndex, imageData) {
    const container = document.getElementById(`opt-images-${optionIndex}`);
    if (!container) return;

    const imageDiv = document.createElement('div');
    imageDiv.className = 'option-image-preview';
    imageDiv.setAttribute('data-image-id', imageData.image_id);

    imageDiv.innerHTML = `
        <img src="${API_URL}/images/${imageData.file_path}"
             alt="Option image"
             style="max-width: 150px; max-height: 100px; border-radius: 4px;">
        <button type="button"
                onclick="deleteOptionImage(${imageData.image_id}, ${optionIndex})"
                class="btn-delete-image"
                title="Удалить изображение">✕</button>
    `;

    container.appendChild(imageDiv);
}

// Удалить изображение варианта ответа
window.deleteOptionImage = async function deleteOptionImage(imageId, optionIndex) {
    if (!confirm('Удалить это изображение?')) return;

    try {
        const response = await fetch(`${API_URL}/images/${imageId}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            // Удаляем из UI
            const container = document.getElementById(`opt-images-${optionIndex}`);
            const imageDiv = container.querySelector(`[data-image-id="${imageId}"]`);
            if (imageDiv) {
                imageDiv.remove();
            }
            alert('✅ Изображение удалено');
        } else {
            alert('❌ Ошибка: ' + result.error);
        }
    } catch (error) {
        console.error('Ошибка удаления изображения:', error);
        alert('❌ Ошибка удаления изображения');
    }
}

// Загрузить существующие изображения для вариантов ответа
window.loadOptionImages = async function loadOptionImages(options) {
    for (let i = 0; i < options.length; i++) {
        const option = options[i];
        if (!option.id) continue;

        try {
            const response = await fetch(`${API_URL}/options/${option.id}/images`);
            const result = await response.json();

            if (result.success && result.images && result.images.length > 0) {
                result.images.forEach(image => {
                    displayOptionImage(i, {
                        image_id: image.id,
                        file_path: image.file_path
                    });
                });
            }
        } catch (error) {
            console.error('Ошибка загрузки изображений варианта:', error);
        }
    }
}

// ============== ФУНКЦИИ ДЛЯ РАБОТЫ С ИЗОБРАЖЕНИЯМИ ПАР СООТВЕТСТВИЯ ==============

// Загрузить изображение для пары соответствия
window.uploadMatchingImage = function uploadMatchingImage(pairId, pairIndex, side) {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/png,image/jpeg,image/jpg,image/gif,image/webp,image/svg+xml';

    input.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        // Проверяем размер файла (макс 5MB)
        if (file.size > 5 * 1024 * 1024) {
            alert('❌ Файл слишком большой. Максимальный размер: 5 МБ');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);
        formData.append('matching_pair_id', pairId);
        formData.append('matching_side', side);
        formData.append('question_id', currentEditingQuestion.id);
        formData.append('image_type', 'matching');

        try {
            const response = await fetch(`${API_URL}/images/upload`, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                displayMatchingImage(pairIndex, side, result);
                alert('✅ Изображение успешно загружено!');
            } else {
                alert('❌ Ошибка: ' + result.error);
            }
        } catch (error) {
            console.error('Ошибка загрузки изображения:', error);
            alert('❌ Ошибка загрузки изображения');
        }
    };

    input.click();
}

// Отобразить изображение пары соответствия
window.displayMatchingImage = function displayMatchingImage(pairIndex, side, imageData) {
    const container = document.getElementById(`pair-${side}-images-${pairIndex}`);
    if (!container) return;

    const imageDiv = document.createElement('div');
    imageDiv.className = 'matching-image-preview';
    imageDiv.setAttribute('data-image-id', imageData.image_id);

    imageDiv.innerHTML = `
        <img src="${API_URL}/images/${imageData.file_path}"
             alt="${side} image"
             style="max-width: 150px; max-height: 100px; border-radius: 4px;">
        <button type="button"
                onclick="deleteMatchingImage(${imageData.image_id}, ${pairIndex}, '${side}')"
                class="btn-delete-image"
                title="Удалить изображение">✕</button>
    `;

    container.appendChild(imageDiv);
}

// Удалить изображение пары соответствия
window.deleteMatchingImage = async function deleteMatchingImage(imageId, pairIndex, side) {
    if (!confirm('Удалить это изображение?')) return;

    try {
        const response = await fetch(`${API_URL}/images/${imageId}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            // Удаляем из UI
            const container = document.getElementById(`pair-${side}-images-${pairIndex}`);
            const imageDiv = container.querySelector(`[data-image-id="${imageId}"]`);
            if (imageDiv) {
                imageDiv.remove();
            }
            alert('✅ Изображение удалено');
        } else {
            alert('❌ Ошибка: ' + result.error);
        }
    } catch (error) {
        console.error('Ошибка удаления изображения:', error);
        alert('❌ Ошибка удаления изображения');
    }
}

// Загрузить существующие изображения для пар соответствия
window.loadMatchingImages = async function loadMatchingImages(pairs) {
    for (let i = 0; i < pairs.length; i++) {
        const pair = pairs[i];
        if (!pair.id) continue;

        try {
            const response = await fetch(`${API_URL}/matching_pairs/${pair.id}/images`);
            const result = await response.json();

            if (result.success && result.images && result.images.length > 0) {
                result.images.forEach(image => {
                    displayMatchingImage(i, image.matching_side, {
                        image_id: image.id,
                        file_path: image.file_path
                    });
                });
            }
        } catch (error) {
            console.error('Ошибка загрузки изображений пары:', error);
        }
    }
}

// ============== ФУНКЦИИ ДЛЯ РАБОТЫ С ИЗОБРАЖЕНИЯМИ ВОПРОСА ==============

// Загрузить изображение для вопроса
window.uploadQuestionImage = function uploadQuestionImage() {
    if (!currentEditingQuestion || !currentEditingQuestion.id) {
        alert('❌ Сначала сохраните вопрос, чтобы добавить изображение');
        return;
    }

    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/png,image/jpeg,image/jpg,image/gif,image/webp,image/svg+xml';

    input.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        // Проверяем размер файла (макс 5MB)
        if (file.size > 5 * 1024 * 1024) {
            alert('❌ Файл слишком большой. Максимальный размер: 5 МБ');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);
        formData.append('question_id', currentEditingQuestion.id);
        formData.append('image_type', 'question');

        try {
            const response = await fetch(`${API_URL}/images/upload`, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                displayQuestionImage(result);
                alert('✅ Изображение успешно загружено!');
            } else {
                alert('❌ Ошибка: ' + result.error);
            }
        } catch (error) {
            console.error('Ошибка загрузки изображения:', error);
            alert('❌ Ошибка загрузки изображения');
        }
    };

    input.click();
}

// Отобразить изображение вопроса
window.displayQuestionImage = function displayQuestionImage(imageData) {
    const container = document.getElementById('question-images');
    if (!container) return;

    const imageDiv = document.createElement('div');
    imageDiv.className = 'question-image-preview';
    imageDiv.setAttribute('data-image-id', imageData.image_id || imageData.id);

    imageDiv.innerHTML = `
        <img src="${API_URL}/images/${imageData.file_path}"
             alt="Question image"
             style="max-width: 200px; max-height: 150px; border-radius: 4px;">
        <button type="button"
                onclick="deleteQuestionImage(${imageData.image_id || imageData.id})"
                class="btn-delete-image"
                title="Удалить изображение">✕</button>
    `;

    container.appendChild(imageDiv);
}

// Удалить изображение вопроса
window.deleteQuestionImage = async function deleteQuestionImage(imageId) {
    if (!confirm('Удалить это изображение?')) return;

    try {
        const response = await fetch(`${API_URL}/images/${imageId}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            // Удаляем из UI
            const container = document.getElementById('question-images');
            const imageDiv = container.querySelector(`[data-image-id="${imageId}"]`);
            if (imageDiv) {
                imageDiv.remove();
            }
            alert('✅ Изображение удалено');
        } else {
            alert('❌ Ошибка: ' + result.error);
        }
    } catch (error) {
        console.error('Ошибка удаления изображения:', error);
        alert('❌ Ошибка удаления изображения');
    }
}

// Загрузить существующие изображения вопроса
window.loadQuestionImages = async function loadQuestionImages(questionId) {
    try {
        const response = await fetch(`${API_URL}/questions/${questionId}/images`);
        const result = await response.json();

        if (result.success && result.images && result.images.length > 0) {
            result.images.forEach(image => {
                displayQuestionImage({
                    id: image.id,
                    image_id: image.id,
                    file_path: image.file_path
                });
            });
        }
    } catch (error) {
        console.error('Ошибка загрузки изображений вопроса:', error);
    }
}
