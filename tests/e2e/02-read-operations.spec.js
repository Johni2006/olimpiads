/**
 * READ Operations Tests (TC_009 - TC_011)
 *
 * Тесты для проверки чтения и просмотра викторин и вопросов.
 *
 * @group read
 */

const { test, expect } = require('../fixtures/base-fixtures');
const { generateRandomQuiz, generateRandomQuestion, TEST_PREFIX } = require('../data/test-data');

test.describe('READ Operations @read', () => {
  /**
   * TC_009: Просмотр списка викторин
   *
   * Проверяет получение списка всех викторин с фильтрацией.
   */
  test('TC_009: Просмотр списка викторин', async ({ api, request }) => {
    console.log('\n📝 Тест TC_009: Просмотр списка викторин');

    // Создаем несколько тестовых викторин
    const quiz1 = await api.createQuiz(request, generateRandomQuiz());
    const quiz2 = await api.createQuiz(request, generateRandomQuiz());
    const quiz3 = await api.createQuiz(request, generateRandomQuiz());

    // Получаем список викторин
    const response = await api.apiRequest(request, '/quizzes', {
      method: 'GET',
    });

    expect(response.status).toBe(200);
    expect(response.data.success).toBe(true);
    expect(response.data.quizzes).toBeDefined();
    expect(Array.isArray(response.data.quizzes)).toBe(true);

    // Проверяем, что наши викторины в списке
    const quizIds = response.data.quizzes.map(q => q.id);
    expect(quizIds).toContain(quiz1.id);
    expect(quizIds).toContain(quiz2.id);
    expect(quizIds).toContain(quiz3.id);

    console.log(`✓ Получено викторин: ${response.data.quizzes.length}`);
  });

  /**
   * TC_010: Просмотр деталей викторины
   *
   * Проверяет получение полной информации о конкретной викторине.
   */
  test('TC_010: Просмотр деталей викторины', async ({ api, request }) => {
    console.log('\n📝 Тест TC_010: Просмотр деталей викторины');

    // Создаем вопросы
    const q1 = await api.createQuestion(request, generateRandomQuestion('choice'));
    const q2 = await api.createQuestion(request, generateRandomQuestion('text'));
    const q3 = await api.createQuestion(request, generateRandomQuestion('multiple_choice'));

    // Создаем викторину с вопросами
    const quizData = {
      ...generateRandomQuiz(),
      question_ids: [q1.id, q2.id, q3.id],
    };
    const quiz = await api.createQuiz(request, quizData);

    // Получаем детали викторины
    const quizDetails = await api.getQuiz(request, quiz.id);

    // Проверяем полноту данных
    expect(quizDetails).toBeDefined();
    expect(quizDetails.id).toBe(quiz.id);
    expect(quizDetails.title).toBe(quizData.title);
    expect(quizDetails.questions).toBeDefined();
    expect(quizDetails.questions.length).toBe(3);
    expect(quizDetails.question_count).toBe(3);

    // Проверяем наличие статистики
    expect(quizDetails.stats).toBeDefined();

    console.log(`✓ Получены детали викторины: "${quizDetails.title}", вопросов: ${quizDetails.questions.length}`);
  });

  /**
   * TC_011: Просмотр вопросов с картинками
   *
   * Проверяет, что изображения корректно отображаются в вопросах.
   */
  test('TC_011: Просмотр вопросов с картинками', async ({ api, request }) => {
    console.log('\n📝 Тест TC_011: Просмотр вопросов с картинками');

    const path = require('path');
    const { testImagePath } = require('../data/test-data');

    // Создаем вопрос
    const question = await api.createQuestion(request, generateRandomQuestion('choice'));

    // Добавляем изображения
    const imagePath = path.resolve(testImagePath);
    const img1 = await api.uploadImage(request, imagePath, {
      question_id: question.id,
      position: 0,
      description: 'Первое изображение',
    });
    const img2 = await api.uploadImage(request, imagePath, {
      question_id: question.id,
      position: 1,
      description: 'Второе изображение',
    });

    // Получаем вопрос с изображениями
    const questionWithImages = await api.getQuestion(request, question.id);

    // Проверяем наличие изображений
    expect(questionWithImages.images).toBeDefined();
    expect(questionWithImages.images.length).toBe(2);

    // Проверяем данные изображений
    const images = questionWithImages.images;
    expect(images[0].file_path).toBeDefined();
    expect(images[0].description).toBe('Первое изображение');
    expect(images[1].description).toBe('Второе изображение');

    console.log(`✓ Вопрос с ${images.length} изображениями загружен корректно`);
  });
});
