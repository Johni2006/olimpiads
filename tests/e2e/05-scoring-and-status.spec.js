/**
 * SCORING & STATUS Tests (TC_021 - TC_027)
 *
 * Тесты для проверки системы оценивания и статусов викторин.
 *
 * @group scoring
 */

const { test, expect } = require('../fixtures/base-fixtures');
const {
  generateRandomQuiz,
  singleChoiceQuestions,
  multipleChoiceQuestions,
  textQuestions,
  students,
} = require('../data/test-data');

test.describe('SCORING & STATUS @scoring', () => {
  /**
   * TC_021: Проверка подсчета баллов (все правильно)
   *
   * Проверяет корректность подсчета баллов при всех правильных ответах.
   */
  test('TC_021: Проверка подсчета баллов (все правильно)', async ({ api, request }) => {
    console.log('\n📝 Тест TC_021: Проверка подсчета баллов (все правильно)');

    // Создаем вопросы
    const q1 = await api.createQuestion(request, {
      ...singleChoiceQuestions[0],
      points: 2.0,
    });
    const q2 = await api.createQuestion(request, {
      ...singleChoiceQuestions[1],
      points: 3.0,
    });

    // Создаем викторину
    const quiz = await api.createQuiz(request, {
      ...generateRandomQuiz(),
      question_ids: [q1.id, q2.id],
      show_correct_answers: true,
    });

    // Начинаем прохождение
    const attempt = await api.startQuizAttempt(request, quiz.unique_code, students[0].name, students[0].email);

    // Отвечаем правильно на все вопросы
    const correctAnswer1 = q1.options.find(opt => opt.is_correct).text;
    await api.submitAnswer(request, attempt.unique_session_id, q1.id, correctAnswer1);

    const correctAnswer2 = q2.options.find(opt => opt.is_correct).text;
    await api.submitAnswer(request, attempt.unique_session_id, q2.id, correctAnswer2);

    // Завершаем викторину
    const results = await api.completeQuizAttempt(request, attempt.unique_session_id);

    // Проверяем результаты
    expect(results.correct_answers).toBe(2);
    expect(results.total_questions).toBe(2);
    expect(results.score).toBe(100); // 100% правильных ответов
    expect(results.points_earned).toBe(5.0); // 2 + 3 балла
    expect(results.points_total).toBe(5.0);

    console.log(`✓ Все ответы правильные: ${results.score}%, баллов: ${results.points_earned}/${results.points_total}`);
  });

  /**
   * TC_022: Проверка подсчета баллов (частично правильно)
   *
   * Проверяет корректность подсчета при частично правильных ответах.
   */
  test('TC_022: Проверка подсчета баллов (частично правильно)', async ({ api, request }) => {
    console.log('\n📝 Тест TC_022: Проверка подсчета баллов (частично правильно)');

    // Создаем вопросы
    const q1 = await api.createQuestion(request, {
      ...singleChoiceQuestions[0],
      points: 1.0,
    });
    const q2 = await api.createQuestion(request, {
      ...textQuestions[0],
      points: 1.0,
    });
    const q3 = await api.createQuestion(request, {
      ...multipleChoiceQuestions[0],
      points: 2.0,
    });

    // Создаем викторину
    const quiz = await api.createQuiz(request, {
      ...generateRandomQuiz(),
      question_ids: [q1.id, q2.id, q3.id],
    });

    // Начинаем прохождение
    const attempt = await api.startQuizAttempt(request, quiz.unique_code, students[1].name);

    // Отвечаем: правильно, неправильно, правильно
    const correctAnswer1 = q1.options.find(opt => opt.is_correct).text;
    await api.submitAnswer(request, attempt.unique_session_id, q1.id, correctAnswer1);

    await api.submitAnswer(request, attempt.unique_session_id, q2.id, 'Неправильный ответ');

    const correctAnswers3 = q3.options.filter(opt => opt.is_correct).map(opt => opt.text);
    await api.submitAnswer(request, attempt.unique_session_id, q3.id, correctAnswers3);

    // Завершаем викторину
    const results = await api.completeQuizAttempt(request, attempt.unique_session_id);

    // Проверяем результаты
    expect(results.correct_answers).toBe(2); // 2 из 3
    expect(results.total_questions).toBe(3);
    expect(Math.round(results.score)).toBe(67); // ~66.67%
    expect(results.points_earned).toBe(3.0); // 1 + 0 + 2

    console.log(`✓ Частично правильно: ${results.correct_answers}/${results.total_questions} (${Math.round(results.score)}%)`);
  });

  /**
   * TC_023: Проверка статуса "Не начато"
   *
   * Проверяет, что новая викторина имеет статус "не начато".
   */
  test('TC_023: Проверка статуса "Не начато"', async ({ api, request }) => {
    console.log('\n📝 Тест TC_023: Проверка статуса "Не начато"');

    // Создаем викторину
    const q1 = await api.createQuestion(request, singleChoiceQuestions[0]);
    const quiz = await api.createQuiz(request, {
      ...generateRandomQuiz(),
      question_ids: [q1.id],
    });

    // Получаем викторину
    const quizData = await api.getQuiz(request, quiz.id);

    // Проверяем, что попыток нет
    expect(quizData.stats.total_attempts).toBe(0);
    expect(quizData.stats.completed_attempts).toBe(0);

    console.log(`✓ Викторина не начата: попыток ${quizData.stats.total_attempts}`);
  });

  /**
   * TC_024: Проверка статуса "В процессе"
   *
   * Проверяет, что незавершенная викторина имеет статус "в процессе".
   */
  test('TC_024: Проверка статуса "В процессе"', async ({ api, request }) => {
    console.log('\n📝 Тест TC_024: Проверка статуса "В процессе"');

    // Создаем викторину с несколькими вопросами
    const q1 = await api.createQuestion(request, singleChoiceQuestions[0]);
    const q2 = await api.createQuestion(request, textQuestions[0]);
    const quiz = await api.createQuiz(request, {
      ...generateRandomQuiz(),
      question_ids: [q1.id, q2.id],
    });

    // Начинаем прохождение
    const attempt = await api.startQuizAttempt(request, quiz.unique_code, students[0].name);

    // Отвечаем только на первый вопрос (не завершаем)
    const correctAnswer1 = q1.options.find(opt => opt.is_correct).text;
    await api.submitAnswer(request, attempt.unique_session_id, q1.id, correctAnswer1);

    // Получаем детали попытки
    const API_BASE_URL = 'http://localhost:5001/api';
    const attemptResponse = await request.get(`${API_BASE_URL}/quizzes/session/${attempt.unique_session_id}`);
    const attemptData = await attemptResponse.json();

    // Проверяем, что попытка не завершена
    expect(attemptData.attempt.completed_at).toBeNull();
    expect(attemptData.attempt.answers.length).toBe(1); // Ответили на 1 из 2

    console.log(`✓ Викторина в процессе: ответов ${attemptData.attempt.answers.length}/${quiz.question_count}`);
  });

  /**
   * TC_025: Проверка статуса "Завершено"
   *
   * Проверяет, что завершенная викторина имеет соответствующий статус.
   */
  test('TC_025: Проверка статуса "Завершено"', async ({ api, request }) => {
    console.log('\n📝 Тест TC_025: Проверка статуса "Завершено"');

    // Создаем викторину
    const q1 = await api.createQuestion(request, singleChoiceQuestions[0]);
    const quiz = await api.createQuiz(request, {
      ...generateRandomQuiz(),
      question_ids: [q1.id],
    });

    // Начинаем и завершаем прохождение
    const attempt = await api.startQuizAttempt(request, quiz.unique_code, students[2].name);
    const correctAnswer = q1.options.find(opt => opt.is_correct).text;
    await api.submitAnswer(request, attempt.unique_session_id, q1.id, correctAnswer);
    const results = await api.completeQuizAttempt(request, attempt.unique_session_id);

    // Получаем детали попытки
    const API_BASE_URL = 'http://localhost:5001/api';
    const attemptResponse = await request.get(`${API_BASE_URL}/quizzes/session/${attempt.unique_session_id}`);
    const attemptData = await attemptResponse.json();

    // Проверяем, что попытка завершена
    expect(attemptData.attempt.completed_at).not.toBeNull();
    expect(attemptData.attempt.score).toBeDefined();

    console.log(`✓ Викторина завершена: score=${attemptData.attempt.score}%`);
  });

  /**
   * TC_026: Проверка статуса "Все правильно"
   *
   * Проверяет идентификацию идеального прохождения (100%).
   */
  test('TC_026: Проверка статуса "Все правильно"', async ({ api, request }) => {
    console.log('\n📝 Тест TC_026: Проверка статуса "Все правильно"');

    // Создаем викторину
    const q1 = await api.createQuestion(request, singleChoiceQuestions[0]);
    const q2 = await api.createQuestion(request, singleChoiceQuestions[1]);
    const quiz = await api.createQuiz(request, {
      ...generateRandomQuiz(),
      question_ids: [q1.id, q2.id],
    });

    // Проходим викторину с 100% результатом
    const attempt = await api.startQuizAttempt(request, quiz.unique_code, 'Perfect Student');

    const correctAnswer1 = q1.options.find(opt => opt.is_correct).text;
    await api.submitAnswer(request, attempt.unique_session_id, q1.id, correctAnswer1);

    const correctAnswer2 = q2.options.find(opt => opt.is_correct).text;
    await api.submitAnswer(request, attempt.unique_session_id, q2.id, correctAnswer2);

    const results = await api.completeQuizAttempt(request, attempt.unique_session_id);

    // Проверяем идеальный результат
    expect(results.score).toBe(100);
    expect(results.correct_answers).toBe(results.total_questions);

    console.log(`✓ Все правильно: ${results.correct_answers}/${results.total_questions} (100%)`);
  });

  /**
   * TC_027: Проверка процента правильных ответов
   *
   * Проверяет корректность расчета процента в различных сценариях.
   */
  test('TC_027: Проверка процента правильных ответов', async ({ api, request }) => {
    console.log('\n📝 Тест TC_027: Проверка процента правильных ответов');

    // Создаем викторину с 5 вопросами
    const questions = await Promise.all([
      api.createQuestion(request, { ...singleChoiceQuestions[0], points: 1 }),
      api.createQuestion(request, { ...singleChoiceQuestions[1], points: 1 }),
      api.createQuestion(request, { ...textQuestions[0], points: 1 }),
      api.createQuestion(request, { ...multipleChoiceQuestions[0], points: 2 }),
      api.createQuestion(request, { ...singleChoiceQuestions[0], points: 1 }),
    ]);

    const quiz = await api.createQuiz(request, {
      ...generateRandomQuiz(),
      question_ids: questions.map(q => q.id),
    });

    // Проходим викторину с 3 правильными из 5 (60%)
    const attempt = await api.startQuizAttempt(request, quiz.unique_code, 'Test Student');

    // Правильно
    await api.submitAnswer(request, attempt.unique_session_id, questions[0].id,
      questions[0].options.find(opt => opt.is_correct).text);

    // Неправильно
    await api.submitAnswer(request, attempt.unique_session_id, questions[1].id, 'Wrong');

    // Правильно
    await api.submitAnswer(request, attempt.unique_session_id, questions[2].id, questions[2].correct_text);

    // Неправильно
    await api.submitAnswer(request, attempt.unique_session_id, questions[3].id, ['Wrong']);

    // Правильно
    await api.submitAnswer(request, attempt.unique_session_id, questions[4].id,
      questions[4].options.find(opt => opt.is_correct).text);

    const results = await api.completeQuizAttempt(request, attempt.unique_session_id);

    // Проверяем процент
    expect(results.correct_answers).toBe(3);
    expect(results.total_questions).toBe(5);
    expect(results.score).toBe(60); // 3/5 = 60%

    console.log(`✓ Процент правильных: ${results.correct_answers}/${results.total_questions} = ${results.score}%`);
  });
});
