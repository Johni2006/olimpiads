/**
 * Quiz Status Tests (TC_020 - TC_025)
 *
 * Тесты для проверки работы со статусами викторин (draft/ready)
 * и добавления вопросов в викторины.
 *
 * @group quiz-status
 */

const { test, expect } = require('../fixtures/base-fixtures');
const {
  singleChoiceQuestions,
  generateRandomQuiz,
  generateRandomQuestion,
} = require('../data/test-data');

test.describe('Quiz Status Operations @quiz-status', () => {
  /**
   * TC_020: Создание викторины без вопросов
   *
   * Проверяет, что можно создать пустую викторину в статусе draft.
   */
  test('TC_020: Создание викторины без вопросов', async ({ api, request }) => {
    console.log('\n📝 Тест TC_020: Создание викторины без вопросов');

    // Создаем викторину без вопросов
    const quizData = {
      ...generateRandomQuiz(),
      question_ids: [], // Пустой список вопросов
      status: 'draft',
    };
    const quiz = await api.createQuiz(request, quizData);

    // Проверяем создание
    expect(quiz).toBeDefined();
    expect(quiz.id).toBeGreaterThan(0);
    expect(quiz.status).toBe('draft');
    expect(quiz.question_count).toBe(0);

    console.log(`✓ Пустая викторина создана с ID: ${quiz.id}, статус: ${quiz.status}`);
  });

  /**
   * TC_021: Добавление вопроса в викторину через API
   *
   * Проверяет новый endpoint для добавления вопросов в викторину.
   */
  test('TC_021: Добавление вопроса в викторину', async ({ api, request }) => {
    console.log('\n📝 Тест TC_021: Добавление вопроса в викторину');

    // Создаем викторину
    const quiz = await api.createQuiz(request, {
      ...generateRandomQuiz(),
      status: 'draft',
    });

    // Создаем вопрос
    const question = await api.createQuestion(request, singleChoiceQuestions[0]);

    // Добавляем вопрос в викторину
    const response = await request.post(`http://localhost:5001/api/quizzes/${quiz.id}/questions`, {
      data: {
        question_id: question.id,
      },
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.success).toBe(true);
    expect(data.quiz.question_count).toBe(1);

    console.log(`✓ Вопрос ${question.id} добавлен в викторину ${quiz.id}`);
  });

  /**
   * TC_022: Изменение статуса викторины на ready
   *
   * Проверяет изменение статуса викторины с draft на ready.
   */
  test('TC_022: Изменение статуса викторины на ready', async ({ api, request }) => {
    console.log('\n📝 Тест TC_022: Изменение статуса на ready');

    // Создаем викторину
    const quiz = await api.createQuiz(request, {
      ...generateRandomQuiz(),
      status: 'draft',
    });

    // Меняем статус на ready
    const response = await request.patch(`http://localhost:5001/api/quizzes/${quiz.id}/status`, {
      data: {
        status: 'ready',
      },
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.success).toBe(true);
    expect(data.quiz.status).toBe('ready');

    console.log(`✓ Статус викторины ${quiz.id} изменен на ready`);
  });

  /**
   * TC_023: Попытка добавить вопрос в готовую викторину
   *
   * Проверяет, что нельзя добавить вопрос в викторину со статусом ready.
   */
  test('TC_023: Блокировка добавления вопросов в готовую викторину', async ({ api, request }) => {
    console.log('\n📝 Тест TC_023: Блокировка добавления в ready викторину');

    // Создаем викторину и сразу переводим в ready
    const quiz = await api.createQuiz(request, {
      ...generateRandomQuiz(),
      status: 'draft',
    });

    // Меняем статус на ready
    await request.patch(`http://localhost:5001/api/quizzes/${quiz.id}/status`, {
      data: { status: 'ready' },
    });

    // Создаем вопрос
    const question = await api.createQuestion(request, singleChoiceQuestions[0]);

    // Пытаемся добавить вопрос
    const response = await request.post(`http://localhost:5001/api/quizzes/${quiz.id}/questions`, {
      data: {
        question_id: question.id,
      },
    });

    expect(response.ok()).toBeFalsy();
    const data = await response.json();
    expect(data.success).toBe(false);

    console.log(`✓ Добавление в ready викторину заблокировано`);
  });

  /**
   * TC_024: Возврат викторины в статус draft
   *
   * Проверяет возможность вернуть викторину из ready в draft.
   */
  test('TC_024: Возврат викторины в draft', async ({ api, request }) => {
    console.log('\n📝 Тест TC_024: Возврат в draft');

    // Создаем викторину в статусе ready
    const quiz = await api.createQuiz(request, {
      ...generateRandomQuiz(),
      status: 'draft',
    });

    // Меняем на ready
    await request.patch(`http://localhost:5001/api/quizzes/${quiz.id}/status`, {
      data: { status: 'ready' },
    });

    // Возвращаем в draft
    const response = await request.patch(`http://localhost:5001/api/quizzes/${quiz.id}/status`, {
      data: { status: 'draft' },
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.success).toBe(true);
    expect(data.quiz.status).toBe('draft');

    console.log(`✓ Викторина ${quiz.id} возвращена в draft`);
  });

  /**
   * TC_025: Фильтрация викторин по статусу
   *
   * Проверяет фильтрацию списка викторин по статусу.
   */
  test('TC_025: Фильтрация викторин по статусу', async ({ api, request }) => {
    console.log('\n📝 Тест TC_025: Фильтрация по статусу');

    // Создаем викторины с разными статусами
    const draftQuiz = await api.createQuiz(request, {
      ...generateRandomQuiz(),
      status: 'draft',
    });

    const readyQuiz = await api.createQuiz(request, {
      ...generateRandomQuiz(),
      status: 'draft',
    });

    await request.patch(`http://localhost:5001/api/quizzes/${readyQuiz.id}/status`, {
      data: { status: 'ready' },
    });

    // Получаем только draft викторины
    const draftResponse = await request.get('http://localhost:5001/api/quizzes?status=draft');
    expect(draftResponse.ok()).toBeTruthy();
    const draftData = await draftResponse.json();
    expect(draftData.success).toBe(true);

    // Проверяем, что все викторины имеют статус draft
    const allDraft = draftData.quizzes.every(q => q.status === 'draft');
    expect(allDraft).toBe(true);

    // Получаем только ready викторины
    const readyResponse = await request.get('http://localhost:5001/api/quizzes?status=ready');
    expect(readyResponse.ok()).toBeTruthy();
    const readyData = await readyResponse.json();
    expect(readyData.success).toBe(true);

    // Проверяем, что все викторины имеют статус ready
    const allReady = readyData.quizzes.every(q => q.status === 'ready');
    expect(allReady).toBe(true);

    console.log(`✓ Фильтрация работает корректно: draft=${draftData.quizzes.length}, ready=${readyData.quizzes.length}`);
  });

  /**
   * TC_026: Добавление нескольких вопросов в викторину
   *
   * Проверяет последовательное добавление нескольких вопросов.
   */
  test('TC_026: Добавление нескольких вопросов', async ({ api, request }) => {
    console.log('\n📝 Тест TC_026: Добавление нескольких вопросов');

    // Создаем викторину
    const quiz = await api.createQuiz(request, {
      ...generateRandomQuiz(),
      status: 'draft',
    });

    // Создаем и добавляем 3 вопроса
    const questions = [];
    for (let i = 0; i < 3; i++) {
      const question = await api.createQuestion(request, {
        ...generateRandomQuestion(),
        text: `Тестовый вопрос ${i + 1} - ${Date.now()}`,
      });
      questions.push(question);

      const response = await request.post(`http://localhost:5001/api/quizzes/${quiz.id}/questions`, {
        data: { question_id: question.id },
      });

      expect(response.ok()).toBeTruthy();
    }

    // Проверяем, что все вопросы добавлены
    const quizResponse = await request.get(`http://localhost:5001/api/quizzes/${quiz.id}`);
    const quizData = await quizResponse.json();
    expect(quizData.quiz.question_count).toBe(3);

    console.log(`✓ Добавлено ${questions.length} вопросов в викторину ${quiz.id}`);
  });

  /**
   * TC_027: Попытка добавить один вопрос дважды
   *
   * Проверяет, что один и тот же вопрос нельзя добавить дважды.
   */
  test('TC_027: Блокировка дублирования вопросов', async ({ api, request }) => {
    console.log('\n📝 Тест TC_027: Блокировка дублирования');

    // Создаем викторину и вопрос
    const quiz = await api.createQuiz(request, {
      ...generateRandomQuiz(),
      status: 'draft',
    });

    const question = await api.createQuestion(request, singleChoiceQuestions[0]);

    // Добавляем вопрос первый раз
    const firstResponse = await request.post(`http://localhost:5001/api/quizzes/${quiz.id}/questions`, {
      data: { question_id: question.id },
    });
    expect(firstResponse.ok()).toBeTruthy();

    // Пытаемся добавить второй раз
    const secondResponse = await request.post(`http://localhost:5001/api/quizzes/${quiz.id}/questions`, {
      data: { question_id: question.id },
    });

    expect(secondResponse.ok()).toBeFalsy();
    const data = await secondResponse.json();
    expect(data.success).toBe(false);

    console.log(`✓ Дублирование вопроса заблокировано`);
  });
});
