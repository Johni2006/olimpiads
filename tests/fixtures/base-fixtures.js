/**
 * Base Fixtures для Playwright тестов
 *
 * Этот файл содержит переиспользуемые фикстуры для тестов.
 * Фикстуры автоматически выполняют setup и teardown операции.
 */

const playwrightTest = require('@playwright/test');
const baseTest = playwrightTest.test;
const expect = playwrightTest.expect;

const { cleanupAllTestData } = require('../utils/cleanup');
const apiHelpers = require('../utils/api-helpers');
const uiHelpers = require('../utils/ui-helpers');

/**
 * Расширенный test с автоматической очисткой после каждого теста
 */
const test = baseTest.extend({
  /**
   * API хелперы доступны в каждом тесте
   */
  api: async ({ request }, use) => {
    await use(apiHelpers);
  },

  /**
   * UI хелперы доступны в каждом тесте
   */
  ui: async ({ page }, use) => {
    await use(uiHelpers);
  },
});

/**
 * Test без автоматической очистки (для ручного управления)
 */
const testNoCleanup = baseTest.extend({
  api: async ({ request }, use) => {
    await use(apiHelpers);
  },
  ui: async ({ page }, use) => {
    await use(uiHelpers);
  },
});

module.exports = { test, testNoCleanup, expect };
