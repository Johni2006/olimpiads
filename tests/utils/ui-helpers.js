/**
 * UI Helper Functions
 *
 * Набор функций для работы с UI элементами в тестах.
 * Эти функции упрощают взаимодействие с интерфейсом приложения.
 */

/**
 * Дождаться загрузки страницы
 * @param {import('@playwright/test').Page} page
 */
async function waitForPageLoad(page) {
  await page.waitForLoadState('domcontentloaded');
  await page.waitForLoadState('networkidle');
}

/**
 * Открыть главную страницу
 * @param {import('@playwright/test').Page} page
 */
async function navigateToHomePage(page) {
  await page.goto('/');
  await waitForPageLoad(page);
}

/**
 * Открыть страницу викторин
 * @param {import('@playwright/test').Page} page
 */
async function navigateToQuizzesPage(page) {
  await page.goto('/');
  await waitForPageLoad(page);

  // Ищем вкладку "Викторины" или кнопку перехода
  const quizTab = page.locator('text=/Викторины|Quizzes/i').first();
  if (await quizTab.isVisible()) {
    await quizTab.click();
    await waitForPageLoad(page);
  }
}

/**
 * Открыть страницу редактирования/создания викторины
 * @param {import('@playwright/test').Page} page
 */
async function navigateToQuizEditPage(page) {
  await page.goto('/edit.html');
  await waitForPageLoad(page);
}

/**
 * Открыть страницу прохождения викторины
 * @param {import('@playwright/test').Page} page
 * @param {string} quizCode - Код викторины
 */
async function navigateToQuizTakingPage(page, quizCode) {
  await page.goto(`/quiz.html?code=${quizCode}`);
  await waitForPageLoad(page);
}

/**
 * СОЗДАНИЕ ВОПРОСОВ ЧЕРЕЗ UI
 */

/**
 * Добавить вопрос с одиночным выбором через UI
 * @param {import('@playwright/test').Page} page
 * @param {Object} questionData
 */
async function addSingleChoiceQuestion(page, questionData) {
  const {
    text = 'Тестовый вопрос с одиночным выбором',
    options = ['Вариант 1', 'Вариант 2', 'Вариант 3'],
    correctIndex = 0,
    points = 1,
  } = questionData;

  // Найти кнопку "Добавить вопрос"
  const addButton = page.locator('button:has-text("Добавить вопрос")');
  await addButton.click();

  // Выбрать тип вопроса "Одиночный выбор"
  const typeSelect = page.locator('select[name="question_type"], select#question-type');
  await typeSelect.selectOption({ label: /одиночный|choice/i });

  // Заполнить текст вопроса
  const questionTextInput = page.locator('textarea[name="question_text"], textarea#question-text');
  await questionTextInput.fill(text);

  // Заполнить баллы
  const pointsInput = page.locator('input[name="points"], input#points');
  if (await pointsInput.isVisible()) {
    await pointsInput.fill(points.toString());
  }

  // Добавить варианты ответа
  for (let i = 0; i < options.length; i++) {
    const optionInput = page.locator(`input[name="option_${i}"], input#option-${i}`);
    await optionInput.fill(options[i]);

    // Отметить правильный ответ
    if (i === correctIndex) {
      const correctRadio = page.locator(`input[type="radio"][value="${i}"]`);
      await correctRadio.check();
    }
  }
}

/**
 * Добавить вопрос с множественным выбором через UI
 * @param {import('@playwright/test').Page} page
 * @param {Object} questionData
 */
async function addMultipleChoiceQuestion(page, questionData) {
  const {
    text = 'Тестовый вопрос с множественным выбором',
    options = ['Вариант 1', 'Вариант 2', 'Вариант 3'],
    correctIndices = [0, 1],
    points = 2,
  } = questionData;

  // Найти кнопку "Добавить вопрос"
  const addButton = page.locator('button:has-text("Добавить вопрос")');
  await addButton.click();

  // Выбрать тип вопроса "Множественный выбор"
  const typeSelect = page.locator('select[name="question_type"], select#question-type');
  await typeSelect.selectOption({ label: /множественный|multiple/i });

  // Заполнить текст вопроса
  const questionTextInput = page.locator('textarea[name="question_text"], textarea#question-text');
  await questionTextInput.fill(text);

  // Заполнить баллы
  const pointsInput = page.locator('input[name="points"], input#points');
  if (await pointsInput.isVisible()) {
    await pointsInput.fill(points.toString());
  }

  // Добавить варианты ответа
  for (let i = 0; i < options.length; i++) {
    const optionInput = page.locator(`input[name="option_${i}"], input#option-${i}`);
    await optionInput.fill(options[i]);

    // Отметить правильные ответы
    if (correctIndices.includes(i)) {
      const correctCheckbox = page.locator(`input[type="checkbox"][value="${i}"]`);
      await correctCheckbox.check();
    }
  }
}

/**
 * Добавить текстовый вопрос через UI
 * @param {import('@playwright/test').Page} page
 * @param {Object} questionData
 */
async function addTextQuestion(page, questionData) {
  const {
    text = 'Тестовый текстовый вопрос',
    correctAnswer = 'правильный ответ',
    points = 1,
  } = questionData;

  // Найти кнопку "Добавить вопрос"
  const addButton = page.locator('button:has-text("Добавить вопрос")');
  await addButton.click();

  // Выбрать тип вопроса "Текстовый ответ"
  const typeSelect = page.locator('select[name="question_type"], select#question-type');
  await typeSelect.selectOption({ label: /текст|text/i });

  // Заполнить текст вопроса
  const questionTextInput = page.locator('textarea[name="question_text"], textarea#question-text');
  await questionTextInput.fill(text);

  // Заполнить правильный ответ
  const correctAnswerInput = page.locator('input[name="correct_answer"], input#correct-answer');
  await correctAnswerInput.fill(correctAnswer);

  // Заполнить баллы
  const pointsInput = page.locator('input[name="points"], input#points');
  if (await pointsInput.isVisible()) {
    await pointsInput.fill(points.toString());
  }
}

/**
 * Добавить вопрос-эссе через UI
 * @param {import('@playwright/test').Page} page
 * @param {Object} questionData
 */
async function addEssayQuestion(page, questionData) {
  const {
    text = 'Тестовый вопрос-эссе',
    guidelines = 'Критерии оценивания',
    points = 5,
  } = questionData;

  // Найти кнопку "Добавить вопрос"
  const addButton = page.locator('button:has-text("Добавить вопрос")');
  await addButton.click();

  // Выбрать тип вопроса "Эссе"
  const typeSelect = page.locator('select[name="question_type"], select#question-type');
  await typeSelect.selectOption({ label: /эссе|essay/i });

  // Заполнить текст вопроса
  const questionTextInput = page.locator('textarea[name="question_text"], textarea#question-text');
  await questionTextInput.fill(text);

  // Заполнить критерии оценивания
  const guidelinesInput = page.locator('textarea[name="guidelines"], textarea#guidelines');
  if (await guidelinesInput.isVisible()) {
    await guidelinesInput.fill(guidelines);
  }

  // Заполнить баллы
  const pointsInput = page.locator('input[name="points"], input#points');
  if (await pointsInput.isVisible()) {
    await pointsInput.fill(points.toString());
  }
}

/**
 * ЗАГРУЗКА ИЗОБРАЖЕНИЙ ЧЕРЕЗ UI
 */

/**
 * Загрузить изображение к вопросу через UI
 * @param {import('@playwright/test').Page} page
 * @param {string} filePath - Путь к файлу изображения
 */
async function uploadImageToQuestion(page, filePath) {
  const fileInput = page.locator('input[type="file"][accept*="image"]');
  await fileInput.setInputFiles(filePath);

  // Ждем загрузки
  await page.waitForTimeout(1000);
}

/**
 * Удалить изображение из вопроса через UI
 * @param {import('@playwright/test').Page} page
 * @param {number} imageIndex - Индекс изображения (0-based)
 */
async function removeImageFromQuestion(page, imageIndex) {
  const deleteButton = page.locator(`button[data-image-index="${imageIndex}"]`).filter({ hasText: /удалить|delete|✕/i });
  await deleteButton.click();

  // Подтвердить удаление если есть диалог
  page.on('dialog', dialog => dialog.accept());
}

/**
 * СОХРАНЕНИЕ И ДЕЙСТВИЯ
 */

/**
 * Сохранить викторину
 * @param {import('@playwright/test').Page} page
 */
async function saveQuiz(page) {
  const saveButton = page.locator('button:has-text("Сохранить")').first();
  await saveButton.click();

  // Дождаться успешного сохранения
  await page.waitForSelector('text=/успешно|success/i', { timeout: 5000 }).catch(() => {});
  await page.waitForTimeout(500);
}

/**
 * Удалить вопрос через UI
 * @param {import('@playwright/test').Page} page
 * @param {number} questionIndex - Индекс вопроса
 */
async function deleteQuestionFromUI(page, questionIndex) {
  const deleteButton = page.locator(`button[data-question-index="${questionIndex}"]`).filter({ hasText: /удалить|delete/i });
  await deleteButton.click();

  // Подтвердить удаление
  page.on('dialog', dialog => dialog.accept());
  await page.waitForTimeout(500);
}

/**
 * ПРОХОЖДЕНИЕ ВИКТОРИНЫ
 */

/**
 * Ответить на вопрос с одиночным выбором
 * @param {import('@playwright/test').Page} page
 * @param {number} optionIndex - Индекс варианта ответа
 */
async function answerSingleChoice(page, optionIndex) {
  const radioButton = page.locator(`input[type="radio"]`).nth(optionIndex);
  await radioButton.check();
}

/**
 * Ответить на вопрос с множественным выбором
 * @param {import('@playwright/test').Page} page
 * @param {Array<number>} optionIndices - Индексы вариантов ответа
 */
async function answerMultipleChoice(page, optionIndices) {
  for (const index of optionIndices) {
    const checkbox = page.locator(`input[type="checkbox"]`).nth(index);
    await checkbox.check();
  }
}

/**
 * Ответить на текстовый вопрос
 * @param {import('@playwright/test').Page} page
 * @param {string} answer - Текст ответа
 */
async function answerTextQuestion(page, answer) {
  const textInput = page.locator('input[type="text"], textarea').first();
  await textInput.fill(answer);
}

/**
 * Перейти к следующему вопросу
 * @param {import('@playwright/test').Page} page
 */
async function goToNextQuestion(page) {
  const nextButton = page.locator('button:has-text("Далее"), button:has-text("Next")');
  await nextButton.click();
  await page.waitForTimeout(500);
}

/**
 * Завершить викторину
 * @param {import('@playwright/test').Page} page
 */
async function submitQuiz(page) {
  const submitButton = page.locator('button:has-text("Завершить"), button:has-text("Submit")');
  await submitButton.click();
  await page.waitForTimeout(1000);
}

/**
 * Получить результат викторины со страницы
 * @param {import('@playwright/test').Page} page
 * @returns {Promise<Object>} - Результаты { score, correctAnswers, totalQuestions }
 */
async function getQuizResults(page) {
  // Ждем появления результатов
  await page.waitForSelector('text=/результат|result|score/i', { timeout: 5000 });

  // Извлекаем данные
  const scoreText = await page.locator('text=/\\d+%|\\d+\\/\\d+/').first().textContent();

  return {
    scoreText,
    // Можно добавить парсинг для получения конкретных значений
  };
}

module.exports = {
  waitForPageLoad,
  navigateToHomePage,
  navigateToQuizzesPage,
  navigateToQuizEditPage,
  navigateToQuizTakingPage,
  addSingleChoiceQuestion,
  addMultipleChoiceQuestion,
  addTextQuestion,
  addEssayQuestion,
  uploadImageToQuestion,
  removeImageFromQuestion,
  saveQuiz,
  deleteQuestionFromUI,
  answerSingleChoice,
  answerMultipleChoice,
  answerTextQuestion,
  goToNextQuestion,
  submitQuiz,
  getQuizResults,
};
