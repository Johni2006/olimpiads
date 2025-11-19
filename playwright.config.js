// @ts-check
const { defineConfig, devices } = require('@playwright/test');

/**
 * Конфигурация Playwright для E2E тестирования системы викторин
 * @see https://playwright.dev/docs/test-configuration
 */
module.exports = defineConfig({
  // Папка с тестами
  testDir: './tests',

  // Максимальное время выполнения одного теста (30 секунд)
  timeout: 30 * 1000,

  // Параллельное выполнение тестов
  fullyParallel: false, // Отключаем для последовательного выполнения

  // Не прерывать все тесты при первой ошибке
  forbidOnly: !!process.env.CI,

  // Количество повторов при падении теста
  retries: process.env.CI ? 2 : 0,

  // Количество параллельных workers
  workers: process.env.CI ? 1 : 1, // По одному worker для избежания конфликтов в БД

  // Репортеры (отчеты о тестировании)
  reporter: [
    ['html', { outputFolder: 'test-results/html-report', open: 'never' }],
    ['json', { outputFile: 'test-results/results.json' }],
    ['list'] // Вывод в консоль
  ],

  // Общие настройки для всех проектов
  use: {
    // Базовый URL приложения
    baseURL: 'http://localhost:8000',

    // Скриншоты только при падении
    screenshot: 'only-on-failure',

    // Видео только при падении
    video: 'retain-on-failure',

    // Трейс только при падении
    trace: 'on-first-retry',

    // Таймаут для действий (клик, заполнение и т.д.)
    actionTimeout: 10 * 1000,
  },

  // Конфигурация проектов (браузеры)
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        // API endpoint для прямых запросов к API
        extraHTTPHeaders: {
          'Accept': 'application/json',
        }
      },
    },

    // Раскомментируйте для тестирования в Firefox
    // {
    //   name: 'firefox',
    //   use: { ...devices['Desktop Firefox'] },
    // },

    // Раскомментируйте для тестирования в Safari
    // {
    //   name: 'webkit',
    //   use: { ...devices['Desktop Safari'] },
    // },
  ],

  // Веб-сервер для запуска перед тестами
  webServer: [
    {
      command: 'cd api && source ../venv/bin/activate && python app.py',
      url: 'http://localhost:5001/api/health',
      reuseExistingServer: !process.env.CI,
      timeout: 120 * 1000,
      stdout: 'pipe',
      stderr: 'pipe',
    },
    {
      command: 'cd web && python -m http.server 8000',
      url: 'http://localhost:8000',
      reuseExistingServer: !process.env.CI,
      timeout: 120 * 1000,
      stdout: 'pipe',
      stderr: 'pipe',
    }
  ],
});
