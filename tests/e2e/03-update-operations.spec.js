/**
 * UPDATE Operations Tests (TC_012 - TC_016)
 *
 * Тесты для проверки редактирования викторин, вопросов и изображений.
 *
 * @group update
 */

const { test, expect } = require('../fixtures/base-fixtures');
const { generateRandomQuiz, generateRandomQuestion, TEST_PREFIX, testImagePath } = require('../data/test-data');
const path = require('path');

test.describe('UPDATE Operations @update', () => {
  /**
   * TC_012: Редактирование названия викторины
   *
   * Проверяет обновление основных полей викторины.
   */
  test('TC_012: Редактирование названия викторины', async ({ api, request }) => {
    console.log('\n📝 Тест TC_012: Редактирование названия викторины');

    // Создаем викторину
    const quiz = await api.createQuiz(request, generateRandomQuiz());
    const originalTitle = quiz.title;

    // Обновляем название
    const newTitle = `${TEST_PREFIX} Обновленное название ${Date.now()}`;
    const newDescription = 'Новое описание викторины';

    const updated = await api.updateQuiz(request, quiz.id, {
      title: newTitle,
      description: newDescription,
    });

    // Проверяем обновление
    expect(updated.title).toBe(newTitle);
    expect(updated.description).toBe(newDescription);
    expect(updated.title).not.toBe(originalTitle);

    console.log(`✓ Название обновлено: "${originalTitle}" → "${newTitle}"`);
  });

  /**
   * TC_013: Редактирование вопроса
   *
   * Проверяет обновление текста и параметров вопроса.
   */
  test('TC_013: Редактирование вопроса', async ({ api, request }) => {
    console.log('\n📝 Тест TC_013: Редактирование вопроса');

    // Создаем вопрос
    const question = await api.createQuestion(request, generateRandomQuestion('choice'));
    const originalText = question.text;
    const originalPoints = question.points;

    // Обновляем вопрос
    const newText = `${TEST_PREFIX} Обновленный текст вопроса ${Date.now()}`;
    const newPoints = 5.0;
    const newDifficulty = 3;

    const updated = await api.updateQuestion(request, question.id, {
      text: newText,
      points: newPoints,
      difficulty: newDifficulty,
    });

    // Проверяем обновление
    expect(updated.text).toBe(newText);
    expect(updated.points).toBe(newPoints);
    expect(updated.difficulty).toBe(newDifficulty);
    expect(updated.text).not.toBe(originalText);

    console.log(`✓ Вопрос обновлен: баллы ${originalPoints} → ${newPoints}, сложность → ${newDifficulty}`);
  });

  /**
   * TC_014: Изменение вариантов ответа
   *
   * Проверяет обновление вариантов ответа в вопросе с выбором.
   */
  test('TC_014: Изменение вариантов ответа', async ({ api, request }) => {
    console.log('\n📝 Тест TC_014: Изменение вариантов ответа');

    // Создаем вопрос с вариантами
    const questionData = generateRandomQuestion('choice');
    const question = await api.createQuestion(request, questionData);

    // Обновляем варианты ответа
    const newOptions = [
      { text: 'Новый вариант A', is_correct: false, position: 0 },
      { text: 'Новый вариант B (правильный)', is_correct: true, position: 1 },
      { text: 'Новый вариант C', is_correct: false, position: 2 },
      { text: 'Новый вариант D', is_correct: false, position: 3 },
    ];

    const updated = await api.updateQuestion(request, question.id, {
      options: newOptions,
    });

    // Проверяем обновление
    expect(updated.options.length).toBe(4);
    const correctOptions = updated.options.filter(opt => opt.is_correct);
    expect(correctOptions.length).toBe(1);
    expect(correctOptions[0].text).toContain('правильный');

    console.log(`✓ Варианты ответа обновлены: ${updated.options.length} вариантов`);
  });

  /**
   * TC_015: Замена изображения
   *
   * Проверяет удаление старого изображения и загрузку нового.
   */
  test('TC_015: Замена изображения', async ({ api, request }) => {
    console.log('\n📝 Тест TC_015: Замена изображения');

    // Создаем вопрос с изображением
    const question = await api.createQuestion(request, generateRandomQuestion('choice'));
    const imagePath = path.resolve(testImagePath);

    const oldImage = await api.uploadImage(request, imagePath, {
      question_id: question.id,
      description: 'Старое изображение',
    });

    // Удаляем старое изображение
    const deleted = await api.deleteImage(request, oldImage.id);
    expect(deleted).toBe(true);

    // Загружаем новое изображение
    const newImage = await api.uploadImage(request, imagePath, {
      question_id: question.id,
      description: 'Новое изображение',
    });

    // Проверяем, что изображение заменено
    const updatedQuestion = await api.getQuestion(request, question.id);
    expect(updatedQuestion.images.length).toBe(1);
    expect(updatedQuestion.images[0].id).toBe(newImage.id);
    expect(updatedQuestion.images[0].description).toBe('Новое изображение');

    console.log(`✓ Изображение заменено: ${oldImage.id} → ${newImage.id}`);
  });

  /**
   * TC_016: Добавление изображения к существующему вопросу
   *
   * Проверяет добавление дополнительных изображений.
   */
  test('TC_016: Добавление изображения к существующему вопросу', async ({ api, request }) => {
    console.log('\n📝 Тест TC_016: Добавление изображения к существующему вопросу');

    // Создаем вопрос БЕЗ изображений
    const question = await api.createQuestion(request, generateRandomQuestion('text'));

    // Проверяем, что изображений нет
    let currentQuestion = await api.getQuestion(request, question.id);
    const initialImageCount = currentQuestion.images?.length || 0;
    expect(initialImageCount).toBe(0);

    // Добавляем первое изображение
    const imagePath = path.resolve(testImagePath);
    const img1 = await api.uploadImage(request, imagePath, {
      question_id: question.id,
      position: 0,
      description: 'Первое добавленное изображение',
    });

    // Добавляем второе изображение
    const img2 = await api.uploadImage(request, imagePath, {
      question_id: question.id,
      position: 1,
      description: 'Второе добавленное изображение',
    });

    // Проверяем, что изображения добавлены
    currentQuestion = await api.getQuestion(request, question.id);
    expect(currentQuestion.images.length).toBe(2);

    console.log(`✓ Добавлено ${currentQuestion.images.length} изображения к существующему вопросу`);
  });
});
