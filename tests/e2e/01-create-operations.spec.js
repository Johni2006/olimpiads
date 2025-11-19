/**
 * CREATE Operations Tests (TC_001 - TC_008)
 *
 * Тесты для проверки создания викторин, вопросов и загрузки изображений.
 *
 * @group create
 */

const { test, expect } = require('../fixtures/base-fixtures');
const {
  singleChoiceQuestions,
  multipleChoiceQuestions,
  textQuestions,
  essayQuestions,
  generateRandomQuestion,
  generateRandomQuiz,
  testImagePath,
} = require('../data/test-data');
const path = require('path');

test.describe('CREATE Operations @create', () => {
  /**
   * TC_001: Создание викторины вручную
   *
   * Проверяет, что можно создать викторину через API с базовыми настройками.
   */
  test('TC_001: Создание викторины вручную', async ({ api, request }) => {
    console.log('\n📝 Тест TC_001: Создание викторины вручную');

    // Создаем тестовую викторину
    const quizData = generateRandomQuiz();
    const quiz = await api.createQuiz(request, quizData);

    // Проверяем, что викторина создана
    expect(quiz).toBeDefined();
    expect(quiz.id).toBeGreaterThan(0);
    expect(quiz.title).toBe(quizData.title);
    expect(quiz.description).toBe(quizData.description);
    expect(quiz.unique_code).toBeDefined();
    expect(quiz.unique_code).toMatch(/^[A-Z0-9]{8}$/); // Код из 8 символов

    console.log(`✓ Викторина создана с ID: ${quiz.id}, код: ${quiz.unique_code}`);
  });

  /**
   * TC_002: Добавление вопроса с одиночным выбором
   *
   * Проверяет создание вопроса типа "choice" с вариантами ответа.
   */
  test('TC_002: Добавление вопроса с одиночным выбором', async ({ api, request }) => {
    console.log('\n📝 Тест TC_002: Добавление вопроса с одиночным выбором');

    const questionData = singleChoiceQuestions[0];
    const question = await api.createQuestion(request, questionData);

    // Проверяем основные поля
    expect(question).toBeDefined();
    expect(question.id).toBeGreaterThan(0);
    expect(question.text).toBe(questionData.text);
    expect(question.type).toBe('choice');

    // Проверяем варианты ответа
    expect(question.options).toBeDefined();
    expect(question.options.length).toBe(questionData.options.length);

    // Проверяем, что есть правильный ответ
    const correctOptions = question.options.filter(opt => opt.is_correct);
    expect(correctOptions.length).toBe(1);

    console.log(`✓ Вопрос создан с ID: ${question.id}, вариантов ответа: ${question.options.length}`);
  });

  /**
   * TC_003: Добавление вопроса с множественным выбором
   *
   * Проверяет создание вопроса типа "multiple_choice" с несколькими правильными ответами.
   */
  test('TC_003: Добавление вопроса с множественным выбором', async ({ api, request }) => {
    console.log('\n📝 Тест TC_003: Добавление вопроса с множественным выбором');

    const questionData = multipleChoiceQuestions[0];
    const question = await api.createQuestion(request, questionData);

    expect(question).toBeDefined();
    expect(question.type).toBe('multiple_choice');

    // Проверяем, что есть несколько правильных ответов
    const correctOptions = question.options.filter(opt => opt.is_correct);
    expect(correctOptions.length).toBeGreaterThan(1);

    console.log(`✓ Вопрос с множественным выбором создан, правильных ответов: ${correctOptions.length}`);
  });

  /**
   * TC_004: Добавление вопроса с текстовым ответом
   *
   * Проверяет создание вопроса типа "text" с правильным текстовым ответом.
   */
  test('TC_004: Добавление вопроса с текстовым ответом', async ({ api, request }) => {
    console.log('\n📝 Тест TC_004: Добавление вопроса с текстовым ответом');

    const questionData = textQuestions[0];
    const question = await api.createQuestion(request, questionData);

    expect(question).toBeDefined();
    expect(question.type).toBe('text');
    expect(question.correct_text).toBe(questionData.correct_text);

    console.log(`✓ Текстовый вопрос создан с правильным ответом: "${question.correct_text}"`);
  });

  /**
   * TC_005: Добавление вопроса с эссе
   *
   * Проверяет создание вопроса типа "essay" с критериями оценивания.
   */
  test('TC_005: Добавление вопроса с эссе', async ({ api, request }) => {
    console.log('\n📝 Тест TC_005: Добавление вопроса с эссе');

    const questionData = essayQuestions[0];
    const question = await api.createQuestion(request, questionData);

    expect(question).toBeDefined();
    expect(question.type).toBe('essay');
    expect(question.points).toBe(questionData.points);

    console.log(`✓ Вопрос-эссе создан с баллами: ${question.points}`);
  });

  /**
   * TC_006: Добавление одной картинки к вопросу
   *
   * Проверяет загрузку одного изображения к вопросу.
   */
  test('TC_006: Добавление одной картинки к вопросу', async ({ api, request }) => {
    console.log('\n📝 Тест TC_006: Добавление одной картинки к вопросу');

    // Создаем вопрос
    const questionData = generateRandomQuestion('choice');
    const question = await api.createQuestion(request, questionData);

    // Загружаем изображение
    const imagePath = path.resolve(testImagePath);
    const imageData = await api.uploadImage(request, imagePath, {
      question_id: question.id,
      image_type: 'diagram',
      description: 'Тестовое изображение',
    });

    expect(imageData).toBeDefined();
    expect(imageData.id).toBeGreaterThan(0);
    expect(imageData.question_id).toBe(question.id);

    // Проверяем, что изображение связано с вопросом
    const updatedQuestion = await api.getQuestion(request, question.id);
    expect(updatedQuestion.images).toBeDefined();
    expect(updatedQuestion.images.length).toBe(1);

    console.log(`✓ Изображение загружено, ID: ${imageData.id}`);
  });

  /**
   * TC_007: Добавление нескольких картинок к вопросу
   *
   * Проверяет загрузку множественных изображений к одному вопросу.
   */
  test('TC_007: Добавление нескольких картинок к вопросу', async ({ api, request }) => {
    console.log('\n📝 Тест TC_007: Добавление нескольких картинок к вопросу');

    // Создаем вопрос
    const questionData = generateRandomQuestion('choice');
    const question = await api.createQuestion(request, questionData);

    // Загружаем 3 изображения
    const imagePath = path.resolve(testImagePath);
    const imageIds = [];

    for (let i = 0; i < 3; i++) {
      const imageData = await api.uploadImage(request, imagePath, {
        question_id: question.id,
        position: i,
        description: `Тестовое изображение ${i + 1}`,
      });
      imageIds.push(imageData.id);
    }

    // Проверяем, что все изображения загружены
    const updatedQuestion = await api.getQuestion(request, question.id);
    expect(updatedQuestion.images).toBeDefined();
    expect(updatedQuestion.images.length).toBe(3);

    console.log(`✓ Загружено ${imageIds.length} изображений`);
  });

  /**
   * TC_008: Загрузка файла с вопросами (через API загрузки PDF)
   *
   * Проверяет загрузку PDF файла и автоматический парсинг вопросов.
   * Примечание: Для полноценного теста нужен реальный PDF файл.
   */
  test.skip('TC_008: Загрузка файла с вопросами', async ({ request }) => {
    console.log('\n📝 Тест TC_008: Загрузка файла с вопросами');

    // TODO: Этот тест требует реальный PDF файл для загрузки
    // Пока помечен как skip

    console.log('⚠️  Тест пропущен - требуется реальный PDF файл');
  });
});
