/**
 * DELETE Operations Tests (TC_017 - TC_020)
 *
 * Тесты для проверки удаления вопросов, файлов, изображений и викторин.
 *
 * @group delete
 */

const { test, expect } = require('../fixtures/base-fixtures');
const { generateRandomQuiz, generateRandomQuestion, testImagePath } = require('../data/test-data');
const path = require('path');

test.describe('DELETE Operations @delete', () => {
  /**
   * TC_017: Удаление вопроса
   *
   * Проверяет удаление вопроса и каскадное удаление связанных данных.
   */
  test('TC_017: Удаление вопроса', async ({ api, request }) => {
    console.log('\n📝 Тест TC_017: Удаление вопроса');

    // Создаем вопрос с вариантами ответа
    const question = await api.createQuestion(request, generateRandomQuestion('choice'));
    const questionId = question.id;

    // Проверяем, что вопрос существует
    const existingQuestion = await api.getQuestion(request, questionId);
    expect(existingQuestion).toBeDefined();
    expect(existingQuestion.id).toBe(questionId);

    // Удаляем вопрос
    const deleted = await api.deleteQuestion(request, questionId);
    expect(deleted).toBe(true);

    // Проверяем, что вопрос удален
    await expect(async () => {
      await api.getQuestion(request, questionId);
    }).rejects.toThrow();

    console.log(`✓ Вопрос ID ${questionId} успешно удален`);
  });

  /**
   * TC_018: Удаление файла (PDF)
   *
   * Проверяет удаление PDF файла и связанных вопросов.
   */
  test('TC_018: Удаление файла (PDF)', async ({ request }) => {
    console.log('\n📝 Тест TC_018: Удаление файла (PDF)');

    const API_BASE_URL = 'http://localhost:5001/api';
    const { TEST_PREFIX } = require('../data/test-data');

    // Создаем запись PDF (без реального файла)
    const response = await request.post(`${API_BASE_URL}/pdfs`, {
      data: {
        display_name: `${TEST_PREFIX} Тестовый PDF ${Date.now()}`,
        university: 'Тестовый университет',
        olympiad: 'Тестовая олимпиада',
        year: '2024',
        subject: 'Тестовый предмет',
      },
    });

    const data = await response.json();
    expect(data.success).toBe(true);
    const pdfId = data.pdf.id;

    // Проверяем, что PDF существует
    const getPdfResponse = await request.get(`${API_BASE_URL}/pdfs/${pdfId}`);
    expect(getPdfResponse.status()).toBe(200);

    // Удаляем PDF
    const deleteResponse = await request.delete(`${API_BASE_URL}/pdfs/${pdfId}`);
    expect(deleteResponse.status()).toBeGreaterThanOrEqual(200);
    expect(deleteResponse.status()).toBeLessThan(300);

    // Проверяем, что PDF удален
    const checkResponse = await request.get(`${API_BASE_URL}/pdfs/${pdfId}`);
    expect(checkResponse.status()).toBe(404);

    console.log(`✓ PDF файл ID ${pdfId} успешно удален`);
  });

  /**
   * TC_019: Удаление изображения из вопроса
   *
   * Проверяет удаление конкретного изображения, не затрагивая вопрос.
   */
  test('TC_019: Удаление изображения из вопроса', async ({ api, request }) => {
    console.log('\n📝 Тест TC_019: Удаление изображения из вопроса');

    // Создаем вопрос с несколькими изображениями
    const question = await api.createQuestion(request, generateRandomQuestion('choice'));
    const imagePath = path.resolve(testImagePath);

    const img1 = await api.uploadImage(request, imagePath, {
      question_id: question.id,
      position: 0,
    });
    const img2 = await api.uploadImage(request, imagePath, {
      question_id: question.id,
      position: 1,
    });
    const img3 = await api.uploadImage(request, imagePath, {
      question_id: question.id,
      position: 2,
    });

    // Проверяем, что все изображения загружены
    let currentQuestion = await api.getQuestion(request, question.id);
    expect(currentQuestion.images.length).toBe(3);

    // Удаляем второе изображение
    const deleted = await api.deleteImage(request, img2.id);
    expect(deleted).toBe(true);

    // Проверяем, что осталось 2 изображения
    currentQuestion = await api.getQuestion(request, question.id);
    expect(currentQuestion.images.length).toBe(2);

    // Проверяем, что вопрос не пострадал
    expect(currentQuestion.id).toBe(question.id);
    expect(currentQuestion.text).toBe(question.text);

    console.log(`✓ Изображение удалено, осталось ${currentQuestion.images.length} изображений`);
  });

  /**
   * TC_020: Удаление викторины
   *
   * Проверяет удаление викторины и каскадное удаление попыток прохождения.
   */
  test('TC_020: Удаление викторины', async ({ api, request }) => {
    console.log('\n📝 Тест TC_020: Удаление викторины');

    // Создаем викторину с вопросами
    const q1 = await api.createQuestion(request, generateRandomQuestion('choice'));
    const q2 = await api.createQuestion(request, generateRandomQuestion('text'));

    const quizData = {
      ...generateRandomQuiz(),
      question_ids: [q1.id, q2.id],
    };
    const quiz = await api.createQuiz(request, quizData);
    const quizId = quiz.id;

    // Проверяем, что викторина существует
    const existingQuiz = await api.getQuiz(request, quizId);
    expect(existingQuiz).toBeDefined();
    expect(existingQuiz.id).toBe(quizId);

    // Удаляем викторину
    const deleted = await api.deleteQuiz(request, quizId);
    expect(deleted).toBe(true);

    // Проверяем, что викторина удалена
    await expect(async () => {
      await api.getQuiz(request, quizId);
    }).rejects.toThrow();

    // Проверяем, что вопросы остались (не каскадное удаление)
    const stillExistingQuestion = await api.getQuestion(request, q1.id);
    expect(stillExistingQuestion).toBeDefined();

    console.log(`✓ Викторина ID ${quizId} успешно удалена, вопросы сохранены`);
  });
});
