/**
 * Тестовые данные для E2E тестов
 *
 * Этот файл содержит готовые наборы данных для использования в тестах.
 */

/**
 * Префикс для всех тестовых данных
 * Используется для идентификации и очистки тестовых записей
 */
const TEST_PREFIX = '[TEST]';

/**
 * Вопросы с одиночным выбором
 */
const singleChoiceQuestions = [
  {
    text: `${TEST_PREFIX} Какая планета самая большая в Солнечной системе?`,
    type: 'choice',
    difficulty: 1,
    points: 1.0,
    options: [
      { text: 'Юпитер', is_correct: true, position: 0 },
      { text: 'Сатурн', is_correct: false, position: 1 },
      { text: 'Уран', is_correct: false, position: 2 },
      { text: 'Нептун', is_correct: false, position: 3 },
    ],
    tags: {
      subject: [`${TEST_PREFIX} Астрономия`],
      university: [`${TEST_PREFIX} Тестовый университет`],
      year: ['2024'],
    },
  },
  {
    text: `${TEST_PREFIX} Сколько континентов на Земле?`,
    type: 'choice',
    difficulty: 1,
    points: 1.0,
    options: [
      { text: '5', is_correct: false, position: 0 },
      { text: '6', is_correct: false, position: 1 },
      { text: '7', is_correct: true, position: 2 },
      { text: '8', is_correct: false, position: 3 },
    ],
    tags: {
      subject: [`${TEST_PREFIX} География`],
      university: [`${TEST_PREFIX} Тестовый университет`],
      year: ['2024'],
    },
  },
];

/**
 * Вопросы с множественным выбором
 */
const multipleChoiceQuestions = [
  {
    text: `${TEST_PREFIX} Какие из следующих языков являются языками программирования?`,
    type: 'multiple_choice',
    difficulty: 2,
    points: 2.0,
    options: [
      { text: 'Python', is_correct: true, position: 0 },
      { text: 'JavaScript', is_correct: true, position: 1 },
      { text: 'HTML', is_correct: false, position: 2 },
      { text: 'Java', is_correct: true, position: 3 },
      { text: 'CSS', is_correct: false, position: 4 },
    ],
    tags: {
      subject: [`${TEST_PREFIX} Информатика`],
      university: [`${TEST_PREFIX} Тестовый университет`],
      year: ['2024'],
    },
  },
];

/**
 * Текстовые вопросы
 */
const textQuestions = [
  {
    text: `${TEST_PREFIX} Какой город является столицей России?`,
    type: 'text',
    difficulty: 1,
    points: 1.0,
    correct_text: 'Москва',
    tags: {
      subject: [`${TEST_PREFIX} География`],
      university: [`${TEST_PREFIX} Тестовый университет`],
      year: ['2024'],
    },
  },
];

/**
 * Вопросы-эссе
 */
const essayQuestions = [
  {
    text: `${TEST_PREFIX} Опишите основные причины Первой мировой войны`,
    type: 'essay',
    difficulty: 4,
    points: 5.0,
    explanation: 'Ожидается анализ политических, экономических и социальных факторов',
    tags: {
      subject: [`${TEST_PREFIX} История`],
      university: [`${TEST_PREFIX} Тестовый университет`],
      year: ['2024'],
    },
  },
];

/**
 * Вопросы на соответствие
 */
const matchingQuestions = [
  {
    text: `${TEST_PREFIX} Сопоставьте страны и их столицы`,
    type: 'matching',
    difficulty: 2,
    points: 3.0,
    matching_pairs: [
      { left_text: 'Франция', right_text: 'Париж', position: 0 },
      { left_text: 'Германия', right_text: 'Берлин', position: 1 },
      { left_text: 'Италия', right_text: 'Рим', position: 2 },
    ],
    tags: {
      subject: [`${TEST_PREFIX} География`],
      university: [`${TEST_PREFIX} Тестовый университет`],
      year: ['2024'],
    },
  },
];

/**
 * Викторины
 */
const quizzes = [
  {
    title: `${TEST_PREFIX} Викторина по естественным наукам`,
    description: 'Тестовая викторина для проверки знаний по естественным наукам',
    created_by: 'test_teacher',
    time_limit: null,
    show_correct_answers: false,
    allow_review: true,
    pass_threshold: 60.0,
    shuffle_questions: false,
    shuffle_options: false,
    max_attempts: 3,
  },
  {
    title: `${TEST_PREFIX} Быстрая викторина`,
    description: 'Короткая тестовая викторина с ограничением времени',
    created_by: 'test_teacher',
    time_limit: 600, // 10 минут
    show_correct_answers: true,
    allow_review: true,
    pass_threshold: 70.0,
    shuffle_questions: true,
    shuffle_options: true,
    max_attempts: 1,
  },
];

/**
 * Студенты для тестирования
 */
const students = [
  {
    name: `${TEST_PREFIX} Иван Иванов`,
    email: 'ivan.test@example.com',
  },
  {
    name: `${TEST_PREFIX} Мария Петрова`,
    email: 'maria.test@example.com',
  },
  {
    name: `${TEST_PREFIX} Алексей Сидоров`,
    email: 'alex.test@example.com',
  },
];

/**
 * Путь к тестовому изображению (создается в тестах)
 */
const testImagePath = 'tests/data/test-image.png';

/**
 * Генерация случайного тестового вопроса
 * @param {string} type - Тип вопроса
 * @returns {Object}
 */
function generateRandomQuestion(type = 'choice') {
  const timestamp = Date.now();

  switch (type) {
    case 'choice':
      return {
        text: `${TEST_PREFIX} Тестовый вопрос ${timestamp}`,
        type: 'choice',
        difficulty: Math.floor(Math.random() * 5) + 1,
        points: 1.0,
        options: [
          { text: 'Вариант A', is_correct: true, position: 0 },
          { text: 'Вариант B', is_correct: false, position: 1 },
          { text: 'Вариант C', is_correct: false, position: 2 },
        ],
        tags: {
          subject: [`${TEST_PREFIX} Тестовый предмет`],
          university: [`${TEST_PREFIX} Тестовый университет`],
          year: ['2024'],
        },
      };

    case 'multiple_choice':
      return multipleChoiceQuestions[0];

    case 'text':
      return {
        ...textQuestions[0],
        text: `${TEST_PREFIX} Тестовый текстовый вопрос ${timestamp}`,
      };

    case 'essay':
      return {
        ...essayQuestions[0],
        text: `${TEST_PREFIX} Тестовое эссе ${timestamp}`,
      };

    case 'matching':
      return matchingQuestions[0];

    default:
      return singleChoiceQuestions[0];
  }
}

/**
 * Генерация случайной викторины
 * @returns {Object}
 */
function generateRandomQuiz() {
  const timestamp = Date.now();
  return {
    title: `${TEST_PREFIX} Викторина ${timestamp}`,
    description: `Тестовая викторина, созданная ${new Date().toISOString()}`,
    created_by: 'test_teacher',
    time_limit: null,
    show_correct_answers: false,
    allow_review: true,
    pass_threshold: 50.0,
    shuffle_questions: false,
    shuffle_options: false,
    max_attempts: 1,
  };
}

module.exports = {
  TEST_PREFIX,
  singleChoiceQuestions,
  multipleChoiceQuestions,
  textQuestions,
  essayQuestions,
  matchingQuestions,
  quizzes,
  students,
  testImagePath,
  generateRandomQuestion,
  generateRandomQuiz,
};
