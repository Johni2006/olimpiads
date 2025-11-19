/**
 * Cleanup Utilities
 *
 * Утилиты для очистки тестовых данных из базы данных.
 * Используются для подготовки чистого состояния перед тестами.
 */

const { TEST_PREFIX } = require('../data/test-data');

/**
 * Очистить все тестовые данные из базы данных
 * @param {import('@playwright/test').APIRequestContext} request - Playwright request context
 * @returns {Promise<Object>} - Статистика удаленных данных
 */
async function cleanupAllTestData(request) {
  const API_BASE_URL = 'http://localhost:5001/api';
  const stats = {
    quizzes: 0,
    questions: 0,
    images: 0,
    errors: [],
  };

  try {
    // 1. Удаляем все тестовые викторины
    console.log('🧹 Очистка тестовых викторин...');
    const quizzesResponse = await request.get(`${API_BASE_URL}/quizzes?limit=1000`);
    const quizzesData = await quizzesResponse.json();

    if (quizzesData.success && quizzesData.quizzes) {
      const testQuizzes = quizzesData.quizzes.filter(q =>
        q.title && q.title.includes(TEST_PREFIX)
      );

      for (const quiz of testQuizzes) {
        try {
          await request.delete(`${API_BASE_URL}/quizzes/${quiz.id}`);
          stats.quizzes++;
          console.log(`  ✓ Удалена викторина: ${quiz.title}`);
        } catch (error) {
          stats.errors.push(`Ошибка удаления викторины ${quiz.id}: ${error.message}`);
          console.error(`  ✗ Ошибка удаления викторины ${quiz.id}`);
        }
      }
    }

    // 2. Удаляем все тестовые вопросы
    console.log('🧹 Очистка тестовых вопросов...');
    const questionsResponse = await request.get(`${API_BASE_URL}/questions?limit=1000`);
    const questionsData = await questionsResponse.json();

    if (questionsData.success && questionsData.questions) {
      const testQuestions = questionsData.questions.filter(q =>
        q.text && q.text.includes(TEST_PREFIX)
      );

      for (const question of testQuestions) {
        try {
          await request.delete(`${API_BASE_URL}/questions/${question.id}`);
          stats.questions++;
          console.log(`  ✓ Удален вопрос: ${question.text.substring(0, 50)}...`);
        } catch (error) {
          stats.errors.push(`Ошибка удаления вопроса ${question.id}: ${error.message}`);
          console.error(`  ✗ Ошибка удаления вопроса ${question.id}`);
        }
      }
    }

    // 3. Очищаем тестовые PDF записи
    console.log('🧹 Очистка тестовых PDF...');
    const pdfsResponse = await request.get(`${API_BASE_URL}/pdfs?limit=1000`);
    const pdfsData = await pdfsResponse.json();

    if (pdfsData.success && pdfsData.pdfs) {
      const testPdfs = pdfsData.pdfs.filter(p =>
        p.display_name && p.display_name.includes(TEST_PREFIX)
      );

      for (const pdf of testPdfs) {
        try {
          await request.delete(`${API_BASE_URL}/pdfs/${pdf.id}`);
          console.log(`  ✓ Удален PDF: ${pdf.display_name}`);
        } catch (error) {
          stats.errors.push(`Ошибка удаления PDF ${pdf.id}: ${error.message}`);
          console.error(`  ✗ Ошибка удаления PDF ${pdf.id}`);
        }
      }
    }

    console.log('\n📊 Статистика очистки:');
    console.log(`  Викторин удалено: ${stats.quizzes}`);
    console.log(`  Вопросов удалено: ${stats.questions}`);
    console.log(`  Ошибок: ${stats.errors.length}`);

    if (stats.errors.length > 0) {
      console.log('\n⚠️  Ошибки при очистке:');
      stats.errors.forEach(err => console.log(`  - ${err}`));
    }

    return stats;
  } catch (error) {
    console.error('❌ Критическая ошибка при очистке:', error.message);
    throw error;
  }
}

/**
 * Очистить тестовые викторины
 * @param {import('@playwright/test').APIRequestContext} request
 * @returns {Promise<number>} - Количество удаленных викторин
 */
async function cleanupTestQuizzes(request) {
  const API_BASE_URL = 'http://localhost:5001/api';
  let count = 0;

  const response = await request.get(`${API_BASE_URL}/quizzes?limit=1000`);
  const data = await response.json();

  if (data.success && data.quizzes) {
    const testQuizzes = data.quizzes.filter(q => q.title && q.title.includes(TEST_PREFIX));

    for (const quiz of testQuizzes) {
      await request.delete(`${API_BASE_URL}/quizzes/${quiz.id}`);
      count++;
    }
  }

  return count;
}

/**
 * Очистить тестовые вопросы
 * @param {import('@playwright/test').APIRequestContext} request
 * @returns {Promise<number>} - Количество удаленных вопросов
 */
async function cleanupTestQuestions(request) {
  const API_BASE_URL = 'http://localhost:5001/api';
  let count = 0;

  const response = await request.get(`${API_BASE_URL}/questions?limit=1000`);
  const data = await response.json();

  if (data.success && data.questions) {
    const testQuestions = data.questions.filter(q => q.text && q.text.includes(TEST_PREFIX));

    for (const question of testQuestions) {
      await request.delete(`${API_BASE_URL}/questions/${question.id}`);
      count++;
    }
  }

  return count;
}

/**
 * Проверить, что тестовые данные очищены
 * @param {import('@playwright/test').APIRequestContext} request
 * @returns {Promise<boolean>} - true если данные очищены
 */
async function verifyCleanup(request) {
  const API_BASE_URL = 'http://localhost:5001/api';

  // Проверяем викторины
  const quizzesResponse = await request.get(`${API_BASE_URL}/quizzes?limit=1000`);
  const quizzesData = await quizzesResponse.json();
  const testQuizzes = quizzesData.quizzes?.filter(q =>
    q.title && q.title.includes(TEST_PREFIX)
  ) || [];

  // Проверяем вопросы
  const questionsResponse = await request.get(`${API_BASE_URL}/questions?limit=1000`);
  const questionsData = await questionsResponse.json();
  const testQuestions = questionsData.questions?.filter(q =>
    q.text && q.text.includes(TEST_PREFIX)
  ) || [];

  const isClean = testQuizzes.length === 0 && testQuestions.length === 0;

  if (!isClean) {
    console.log(`⚠️  Найдены неочищенные данные: викторин=${testQuizzes.length}, вопросов=${testQuestions.length}`);
  }

  return isClean;
}

module.exports = {
  cleanupAllTestData,
  cleanupTestQuizzes,
  cleanupTestQuestions,
  verifyCleanup,
};
