/**
 * API Helper Functions
 *
 * Набор функций для работы с API в тестах.
 * Эти функции упрощают создание, обновление и удаление данных через API.
 */

const API_BASE_URL = 'http://localhost:5001/api';

/**
 * Выполнить HTTP запрос к API
 * @param {import('@playwright/test').APIRequestContext} request - Playwright request context
 * @param {string} endpoint - API endpoint (например, '/questions')
 * @param {Object} options - Опции запроса (method, data и т.д.)
 * @returns {Promise<Object>} - Ответ API
 */
async function apiRequest(request, endpoint, options = {}) {
  const {
    method = 'GET',
    data = null,
    headers = {},
  } = options;

  const url = `${API_BASE_URL}${endpoint}`;

  const requestOptions = {
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
  };

  if (data) {
    requestOptions.data = data;
  }

  let response;
  switch (method.toUpperCase()) {
    case 'GET':
      response = await request.get(url, requestOptions);
      break;
    case 'POST':
      response = await request.post(url, requestOptions);
      break;
    case 'PUT':
      response = await request.put(url, requestOptions);
      break;
    case 'DELETE':
      response = await request.delete(url, requestOptions);
      break;
    default:
      throw new Error(`Unsupported HTTP method: ${method}`);
  }

  const responseData = await response.json();
  return { status: response.status(), data: responseData };
}

/**
 * СОЗДАНИЕ ДАННЫХ
 */

/**
 * Создать тестовый вопрос через API
 * @param {import('@playwright/test').APIRequestContext} request
 * @param {Object} questionData - Данные вопроса
 * @returns {Promise<Object>} - Созданный вопрос
 */
async function createQuestion(request, questionData) {
  const defaultData = {
    text: 'Тестовый вопрос',
    type: 'choice',
    difficulty: 1,
    points: 1.0,
    options: [
      { text: 'Вариант 1', is_correct: true, position: 0 },
      { text: 'Вариант 2', is_correct: false, position: 1 },
      { text: 'Вариант 3', is_correct: false, position: 2 },
    ],
    tags: {
      subject: ['Тестовый предмет'],
      university: ['Тестовый университет'],
      year: ['2024'],
    },
  };

  const merged = { ...defaultData, ...questionData };
  const response = await apiRequest(request, '/questions', {
    method: 'POST',
    data: merged,
  });

  if (response.status !== 201 && response.status !== 200) {
    throw new Error(`Failed to create question: ${JSON.stringify(response.data)}`);
  }

  return response.data.question || response.data;
}

/**
 * Создать тестовую викторину через API
 * @param {import('@playwright/test').APIRequestContext} request
 * @param {Object} quizData - Данные викторины
 * @returns {Promise<Object>} - Созданная викторина
 */
async function createQuiz(request, quizData) {
  const defaultData = {
    title: 'Тестовая викторина',
    description: 'Описание тестовой викторины',
    created_by: 'test_user',
    question_ids: [],
    time_limit: null,
    show_correct_answers: false,
    allow_review: true,
    pass_threshold: 0.0,
    shuffle_questions: false,
    shuffle_options: false,
    max_attempts: null,
    is_active: true,
  };

  const merged = { ...defaultData, ...quizData };
  const response = await apiRequest(request, '/quizzes', {
    method: 'POST',
    data: merged,
  });

  if (response.status !== 201 && response.status !== 200) {
    throw new Error(`Failed to create quiz: ${JSON.stringify(response.data)}`);
  }

  return response.data.quiz || response.data;
}

/**
 * Загрузить изображение через API
 * @param {import('@playwright/test').APIRequestContext} request
 * @param {string} filePath - Путь к файлу изображения
 * @param {Object} metadata - Метаданные (question_id, option_id и т.д.)
 * @returns {Promise<Object>} - Данные загруженного изображения
 */
async function uploadImage(request, filePath, metadata = {}) {
  const fs = require('fs');
  const path = require('path');

  const formData = new FormData();
  const fileBuffer = fs.readFileSync(filePath);
  const fileName = path.basename(filePath);

  formData.append('file', new Blob([fileBuffer]), fileName);

  // Добавляем метаданные
  Object.keys(metadata).forEach(key => {
    formData.append(key, metadata[key]);
  });

  const response = await request.post(`${API_BASE_URL}/images/upload`, {
    multipart: formData,
  });

  const data = await response.json();
  if (response.status() !== 200 && response.status() !== 201) {
    throw new Error(`Failed to upload image: ${JSON.stringify(data)}`);
  }

  return data;
}

/**
 * ПОЛУЧЕНИЕ ДАННЫХ
 */

/**
 * Получить вопрос по ID
 * @param {import('@playwright/test').APIRequestContext} request
 * @param {number} questionId
 * @returns {Promise<Object>}
 */
async function getQuestion(request, questionId) {
  const response = await apiRequest(request, `/questions/${questionId}`);
  if (response.status !== 200) {
    throw new Error(`Failed to get question: ${JSON.stringify(response.data)}`);
  }
  return response.data.question || response.data;
}

/**
 * Получить викторину по ID
 * @param {import('@playwright/test').APIRequestContext} request
 * @param {number} quizId
 * @returns {Promise<Object>}
 */
async function getQuiz(request, quizId) {
  const response = await apiRequest(request, `/quizzes/${quizId}`);
  if (response.status !== 200) {
    throw new Error(`Failed to get quiz: ${JSON.stringify(response.data)}`);
  }
  return response.data.quiz || response.data;
}

/**
 * ОБНОВЛЕНИЕ ДАННЫХ
 */

/**
 * Обновить вопрос
 * @param {import('@playwright/test').APIRequestContext} request
 * @param {number} questionId
 * @param {Object} updates - Обновления
 * @returns {Promise<Object>}
 */
async function updateQuestion(request, questionId, updates) {
  const response = await apiRequest(request, `/questions/${questionId}`, {
    method: 'PUT',
    data: updates,
  });

  if (response.status !== 200) {
    throw new Error(`Failed to update question: ${JSON.stringify(response.data)}`);
  }

  return response.data.question || response.data;
}

/**
 * Обновить викторину
 * @param {import('@playwright/test').APIRequestContext} request
 * @param {number} quizId
 * @param {Object} updates - Обновления
 * @returns {Promise<Object>}
 */
async function updateQuiz(request, quizId, updates) {
  const response = await apiRequest(request, `/quizzes/${quizId}`, {
    method: 'PUT',
    data: updates,
  });

  if (response.status !== 200) {
    throw new Error(`Failed to update quiz: ${JSON.stringify(response.data)}`);
  }

  return response.data.quiz || response.data;
}

/**
 * УДАЛЕНИЕ ДАННЫХ
 */

/**
 * Удалить вопрос
 * @param {import('@playwright/test').APIRequestContext} request
 * @param {number} questionId
 * @returns {Promise<boolean>}
 */
async function deleteQuestion(request, questionId) {
  const response = await apiRequest(request, `/questions/${questionId}`, {
    method: 'DELETE',
  });

  return response.status === 200 || response.status === 204;
}

/**
 * Удалить викторину
 * @param {import('@playwright/test').APIRequestContext} request
 * @param {number} quizId
 * @returns {Promise<boolean>}
 */
async function deleteQuiz(request, quizId) {
  const response = await apiRequest(request, `/quizzes/${quizId}`, {
    method: 'DELETE',
  });

  return response.status === 200 || response.status === 204;
}

/**
 * Удалить изображение
 * @param {import('@playwright/test').APIRequestContext} request
 * @param {number} imageId
 * @returns {Promise<boolean>}
 */
async function deleteImage(request, imageId) {
  const response = await apiRequest(request, `/images/${imageId}`, {
    method: 'DELETE',
  });

  return response.status === 200 || response.status === 204;
}

/**
 * ПРОХОЖДЕНИЕ ВИКТОРИНЫ
 */

/**
 * Начать прохождение викторины
 * @param {import('@playwright/test').APIRequestContext} request
 * @param {string} quizCode - Уникальный код викторины
 * @param {string} studentName - Имя студента
 * @param {string} studentEmail - Email студента (опционально)
 * @returns {Promise<Object>} - Данные сессии с unique_session_id
 */
async function startQuizAttempt(request, quizCode, studentName, studentEmail = null) {
  const response = await apiRequest(request, `/quizzes/${quizCode}/start`, {
    method: 'POST',
    data: {
      student_name: studentName,
      student_email: studentEmail,
    },
  });

  if (response.status !== 200 && response.status !== 201) {
    throw new Error(`Failed to start quiz: ${JSON.stringify(response.data)}`);
  }

  return response.data.attempt || response.data;
}

/**
 * Отправить ответ на вопрос
 * @param {import('@playwright/test').APIRequestContext} request
 * @param {string} sessionId - ID сессии
 * @param {number} questionId - ID вопроса
 * @param {string|Array} answer - Ответ
 * @param {number} timeSpent - Время, затраченное на ответ (секунды)
 * @returns {Promise<Object>}
 */
async function submitAnswer(request, sessionId, questionId, answer, timeSpent = 0) {
  const response = await apiRequest(request, `/quizzes/session/${sessionId}/answer`, {
    method: 'POST',
    data: {
      question_id: questionId,
      answer: JSON.stringify(answer),
      time_spent: timeSpent,
    },
  });

  if (response.status !== 200) {
    throw new Error(`Failed to submit answer: ${JSON.stringify(response.data)}`);
  }

  return response.data;
}

/**
 * Завершить прохождение викторины
 * @param {import('@playwright/test').APIRequestContext} request
 * @param {string} sessionId - ID сессии
 * @returns {Promise<Object>} - Результаты
 */
async function completeQuizAttempt(request, sessionId) {
  const response = await apiRequest(request, `/quizzes/session/${sessionId}/complete`, {
    method: 'POST',
  });

  if (response.status !== 200) {
    throw new Error(`Failed to complete quiz: ${JSON.stringify(response.data)}`);
  }

  return response.data;
}

module.exports = {
  apiRequest,
  createQuestion,
  createQuiz,
  uploadImage,
  getQuestion,
  getQuiz,
  updateQuestion,
  updateQuiz,
  deleteQuestion,
  deleteQuiz,
  deleteImage,
  startQuizAttempt,
  submitAnswer,
  completeQuizAttempt,
};
