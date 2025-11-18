#!/usr/bin/env python3
"""
Умный загрузчик материалов олимпиад с Selenium
Поддерживает: полная загрузка + обновление (только новые файлы)

УСТАНОВКА (1 минута):
    pip install selenium requests beautifulsoup4 webdriver-manager

ЗАПУСК:
    # Первый раз - скачать всё
    python olympiad_downloader.py --full
    
    # Обновление - только новые материалы
    python olympiad_downloader.py --update
    
    # Тестовый режим (не скачивает)
    python olympiad_downloader.py --dry

СТРУКТУРА:
    olympiads/
    ├── database.json          # База скачанных файлов
    ├── downloads/             # Все файлы
    │   ├── МГУ_Ломоносов/
    │   ├── ВСОШ/
    │   └── ВШЭ/
    └── logs/
        └── download.log
"""

import os
import re
import json
import time
import hashlib
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# Selenium импорты
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# ==================== КОНФИГУРАЦИЯ ====================

# Предметы для поиска
SUBJECTS = [
    "религиоведение", "обществознание", "философия", "право",
    "политология", "социология", "экономика", "история",
    "финансовая грамотность", "основы бизнеса",
    "журналистика", "иностранный язык", "английский"]

# Ключевые слова
ANSWER_KEYWORDS = ["ответ", "решени", "критери", "ключ", "разбор"]
TASK_KEYWORDS = ["задани", "вариант", "тур", "этап"]

# Расширения файлов
FILE_EXTENSIONS = (".pdf", ".zip", ".doc", ".docx")

# Регулярка для года
YEAR_PATTERN = re.compile(r"20\d{2}")

# Источники олимпиад
OLYMPIAD_SOURCES = {
    "МГУ_Ломоносов": {
        "urls": [
            "https://olymp.msu.ru/rus/page/main/29/page/zadaniya-olimpiady-proshlyh-let",  # Религиоведение
            "https://olymp.msu.ru/rus/page/main/77/page/zadaniya-olimpiady-proshlyh-let",  # Обществознание
            "https://olymp.msu.ru/rus/page/main/217/page/zadaniya-olimpiady-proshlyh-let", # Философия
            "https://olymp.msu.ru/rus/page/main/31/page/zadaniya-olimpiady-proshlyh-let",  # Право
            "https://olymp.msu.ru/rus/page/main/86/page/zadaniya-olimpiady-proshlyh-let",  # Политология
        ],
        "type": "selenium"  # Требует JavaScript
    },
    "ВСОШ": {
        "urls": [
            "https://vos.olimpiada.ru/main/table/tasks/",
        ],
        "type": "selenium"
    },
    "ВШЭ": {
        "urls": [
            "https://olymp.hse.ru/mmo/archive",         # Общий архив
            "https://olymp.hse.ru/mmo/tasks-soc",       # Обществознание - задания
            "https://olymp.hse.ru/mmo/tasks-phil",      # Философия - задания
            "https://olymp.hse.ru/mmo/tasks-law",       # Право - задания
            "https://olymp.hse.ru/mmo/tasks-history",   # История - задания
            "https://olymp.hse.ru/mmo/tasks-journ",     # Журналистика - задания
            "https://olymp.hse.ru/mmo/tasks-lang",      # Иностранные языки - задания
            "https://olymp.hse.ru/mmo/tasks-eco",       # Экономика - задания
            "https://olymp.hse.ru/mmo/tasks-pol",       # Политология - задания
            "https://olymp.hse.ru/mmo/tasks-business",  # Основы бизнеса - задания
            "https://olymp.hse.ru/mmo/tasks-finlit",    # Финансовая грамотность - задания
            "https://olymp.hse.ru/mmo/sociology",       # Социология - общая страница
            "https://olymp.hse.ru/mmo/soc",             # Обществознание - главная
            "https://olymp.hse.ru/mmo/phil",            # Философия - главная
            "https://olymp.hse.ru/mmo/law",             # Право - главная
            "https://olymp.hse.ru/mmo/history",         # История - главная
            "https://olymp.hse.ru/mmo/journ",           # Журналистика - главная
            "https://olymp.hse.ru/mmo/eco",             # Экономика - главная
            "https://olymp.hse.ru/mmo/lang",            # Иностранные языки - главная
        ],
        "type": "selenium"
    },
    "РАНХиГС": {
        "urls": [
            "https://www.ranepa.ru/olymp/arkhiv-zadaniy/",
            "https://olymp.ranepa.ru/",
            "https://www.ranepa.ru/shkolnik/olimpiada/",
        ],
        "type": "selenium"  # Требует JavaScript
    },
    "СПбГУ": {
        "urls": [
            "https://olymp.spbu.ru/",
            "https://olymp.spbu.ru/pages/main_main_pair_ol_stage_files-13",
        ],
        "type": "selenium"
    },
    "МГИМО": {
        "urls": [
            "https://olymp.mgimo.ru/",
        ],
        "type": "selenium"
    },
    "МОШ": {
        "urls": [
            "https://mos.olimpiada.ru/",
            "https://mos.olimpiada.ru/tasks/fingram",  # Финансовая грамотность
            "https://mos.olimpiada.ru/olymp/law",      # Право
            "https://mos.olimpiada.ru/olymp/soc",      # Обществознание
        ],
        "type": "selenium"
    },
    "Миссия_выполнима": {
        "urls": [
            "https://mission.fa.ru/",
        ],
        "type": "selenium"
    },
    "Фемида": {
        "urls": [
            "https://rgup.ru/pages/olimp",
        ],
        "type": "selenium"
    },
    "В_мир_права": {
        "urls": [
            "https://rpa-mu.wixsite.com/my-site",
            "https://olimp-lk.rpa-mu.ru/",
        ],
        "type": "selenium"
    },
    "ПВГ": {
        "urls": [
            "https://pvg.mk.ru/",
            "https://pvg.mk.ru/archive/archive/",
        ],
        "type": "selenium"
    },
    "Океан_знаний": {
        "urls": [
            "https://olympiada.eduprosvet.ru/ocean/",
        ],
        "type": "selenium"
    },
    "Изумруд": {
        "urls": [
            "https://izumrud.urfu.ru/ru/",
        ],
        "type": "selenium"
    },
    "РГГУ": {
        "urls": [
            "https://rsuh.ru/education/cdo/",
            "https://rsuh.ru/education/cdo/olimp-archive.php",
        ],
        "type": "selenium"
    },
    "Кутафинская": {
        "urls": [
            "https://msal.ru/",
            "https://msalkirov.ru/olympiade/",
        ],
        "type": "selenium"
    },
    "Толстовская": {
        "urls": [
            "https://olymp.tsput.ru/",
        ],
        "type": "selenium"
    },
    "Вернадский": {
        "urls": [
            "https://vernadsky.online/",
        ],
        "type": "selenium"
    },
    "КФУ": {
        "urls": [
            "https://malun.kpfu.ru/mpo",
        ],
        "type": "selenium"
    },
}

# ==================== НАСТРОЙКА ЛОГИРОВАНИЯ ====================

def setup_logging(log_dir: Path):
    """Настройка логирования"""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"download_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

# ==================== БАЗА ДАННЫХ ====================

class Database:
    """Простая JSON база данных для отслеживания скачанных файлов"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.data = self._load()
    
    def _load(self) -> Dict:
        """Загрузить базу"""
        if self.db_path.exists():
            with open(self.db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"files": {}, "last_update": None, "stats": {}}
    
    def save(self):
        """Сохранить базу"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.data["last_update"] = datetime.now().isoformat()
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def is_downloaded(self, url: str) -> bool:
        """Проверить, скачан ли файл"""
        file_hash = hashlib.md5(url.encode()).hexdigest()
        return file_hash in self.data["files"]
    
    def add_file(self, url: str, file_info: Dict):
        """Добавить информацию о файле"""
        file_hash = hashlib.md5(url.encode()).hexdigest()
        file_info["downloaded_at"] = datetime.now().isoformat()
        self.data["files"][file_hash] = file_info
    
    def get_stats(self) -> Dict:
        """Получить статистику"""
        return self.data.get("stats", {})
    
    def update_stats(self, org: str, subject: str):
        """Обновить статистику"""
        if "stats" not in self.data:
            self.data["stats"] = {}
        key = f"{org}_{subject}"
        self.data["stats"][key] = self.data["stats"].get(key, 0) + 1

# ==================== SELENIUM ДРАЙВЕР ====================

def create_driver(headless: bool = True) -> webdriver.Chrome:
    """Создать Selenium драйвер"""
    options = Options()
    
    if headless:
        options.add_argument("--headless")  # Без окна браузера
    
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    # Автоматическая установка ChromeDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    return driver

# ==================== ПАРСИНГ ====================

def extract_year(text: str) -> Optional[str]:
    """Извлечь год из текста"""
    matches = YEAR_PATTERN.findall(text)
    if matches:
        # Берём самый поздний год
        return max(matches)
    return None

def detect_subject(text: str) -> Optional[str]:
    """Определить предмет"""
    text_lower = text.lower()
    for subject in SUBJECTS:
        if subject in text_lower:
            return subject.capitalize()
    return None

def is_answer_material(text: str) -> bool:
    """Проверить, содержит ли материал ответы"""
    text_lower = text.lower()
    return any(kw in text_lower for kw in ANSWER_KEYWORDS)

def normalize_filename(name: str, extension: str = "", url: str = None) -> str:
    """Нормализовать имя файла"""
    # Убираем недопустимые символы
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = re.sub(r'\s+', ' ', name).strip()
    name = name[:150]  # Ограничение длины

     # Если имя пустое или слишком общее
    if not name or name in ["текст", "прак", "теор", "file"] or len(name) < 5:
        # Добавляем хеш URL для уникальности
        if url:
            url_hash = hashlib.md5(url.encode()).hexdigest()[:6]
            name = f"file_{url_hash}"
        else:
            name = "file"

    # Проверяем общие названия с расширением
    if name.replace('.pdf', '') in ["текст", "прак", "теор"] or len(name.replace('.pdf', '')) < 5:
        if url:
            url_hash = hashlib.md5(url.encode()).hexdigest()[:6]
            name = f"{name.replace('.pdf', '')}_{url_hash}"

    # Добавляем расширение если нужно
    if extension and not name.endswith(extension):
        name += extension

    return name

# ==================== СБОР ССЫЛОК ====================

def collect_links_selenium(driver: webdriver.Chrome, url: str, logger) -> List[Dict]:
    """Собрать ссылки с помощью Selenium (для JS страниц)"""
    logger.info(f"Загрузка страницы: {url}")
    
    try:
        driver.get(url)
        time.sleep(3)  # Ждём загрузки JavaScript
        
        # Прокручиваем страницу вниз для ленивой загрузки
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        # Ищем все ссылки
        links = []
        elements = driver.find_elements(By.TAG_NAME, "a")
        
        for elem in elements:
            try:
                href = elem.get_attribute("href")
                text = elem.text.strip()
                
                if not href:
                    continue
                
                # Проверяем расширение
                if any(href.lower().endswith(ext) for ext in FILE_EXTENSIONS):
                    links.append({
                        "url": href,
                        "text": text,
                        "page_url": url
                    })
            except:
                continue
        
        logger.info(f"Найдено ссылок на файлы: {len(links)}")
        return links
        
    except Exception as e:
        logger.error(f"Ошибка при загрузке {url}: {e}")
        return []

def collect_links_requests(url: str, logger) -> List[Dict]:
    """Собрать ссылки с помощью requests (для простых страниц)"""
    logger.info(f"Загрузка страницы (requests): {url}")
    
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        links = []
        
        for a in soup.find_all("a", href=True):
            href = urljoin(url, a["href"])
            text = a.get_text(strip=True)
            
            if any(href.lower().endswith(ext) for ext in FILE_EXTENSIONS):
                links.append({
                    "url": href,
                    "text": text,
                    "page_url": url
                })
        
        logger.info(f"Найдено ссылок на файлы: {len(links)}")
        return links
        
    except Exception as e:
        logger.error(f"Ошибка при загрузке {url}: {e}")
        return []

# ==================== СКАЧИВАНИЕ ====================

def download_file(url: str, dest_path: Path, logger) -> bool:
    """Скачать файл"""
    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Сначала проверяем доступность
        resp = requests.head(url, timeout=10, allow_redirects=True)
        if resp.status_code == 404:
            logger.warning(f"⚠ Файл недоступен (404): {url}")
            return False
        
        # Теперь скачиваем
        resp = requests.get(url, timeout=60, stream=True)
        resp.raise_for_status()
        
        with open(dest_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        
        size_mb = dest_path.stat().st_size / (1024 * 1024)
        logger.info(f"✓ Скачано ({size_mb:.2f} MB): {dest_path.name}")
        return True
        
    except Exception as e:
        logger.error(f"✗ Ошибка скачивания {url}: {e}")
        return False

# ==================== ГЛАВНАЯ ФУНКЦИЯ ====================

def main():
    parser = argparse.ArgumentParser(description="Умный загрузчик олимпиад с Selenium")
    parser.add_argument("--full", action="store_true", help="Полная загрузка (первый запуск)")
    parser.add_argument("--update", action="store_true", help="Обновление (только новые)")
    parser.add_argument("--dry", action="store_true", help="Тестовый режим (не скачивать)")
    parser.add_argument("--out", default="olympiads", help="Папка для сохранения")
    parser.add_argument("--headless", action="store_true", default=True, help="Браузер без окна")
    
    args = parser.parse_args()
    
    # Если не указан режим, по умолчанию --update
    if not args.full and not args.update:
        args.update = True
    
    # Создаём структуру папок
    base_dir = Path(args.out)
    downloads_dir = base_dir / "downloads"
    logs_dir = base_dir / "logs"
    db_path = base_dir / "database.json"
    
    # Настройка логирования
    logger = setup_logging(logs_dir)
    logger.info("="*60)
    logger.info("СТАРТ ЗАГРУЗЧИКА ОЛИМПИАД")
    logger.info(f"Режим: {'ПОЛНАЯ ЗАГРУЗКА' if args.full else 'ОБНОВЛЕНИЕ'}")
    logger.info(f"Тестовый режим: {args.dry}")
    logger.info("="*60)
    
    # База данных
    db = Database(db_path)
    logger.info(f"Загружена база данных. Файлов в базе: {len(db.data['files'])}")
    
    # Создаём Selenium драйвер
    driver = None
    if not args.dry:
        logger.info("Инициализация Selenium драйвера...")
        driver = create_driver(headless=args.headless)
    
    try:
        total_found = 0
        total_downloaded = 0
        total_skipped = 0
        
        # Обходим все источники
        for org_name, config in OLYMPIAD_SOURCES.items():
            logger.info(f"\n{'='*60}")
            logger.info(f"ОБРАБОТКА: {org_name}")
            logger.info(f"{'='*60}")
            
            all_links = []
            
            # Собираем ссылки со всех URL
            for url in config["urls"]:
                if config["type"] == "selenium" and driver:
                    links = collect_links_selenium(driver, url, logger)
                else:
                    links = collect_links_requests(url, logger)
                
                all_links.extend(links)
                time.sleep(2)  # Пауза между запросами
            
            logger.info(f"Всего найдено файлов для {org_name}: {len(all_links)}")
            total_found += len(all_links)
            
            # Обрабатываем каждую ссылку
            for link_info in all_links:
                url = link_info["url"]
                text = link_info["text"]
                
                # Проверяем, скачан ли уже
                if db.is_downloaded(url):
                    if args.full:
                        # В режиме --full скачиваем всё заново
                        pass
                    else:
                        # В режиме --update пропускаем
                        logger.debug(f"Пропущен (уже скачан): {url}")
                        total_skipped += 1
                        continue
                
                # Определяем метаданные
                year = extract_year(text + " " + url) or "unknown"
                subject = detect_subject(text + " " + url) or "unknown"
                has_answers = is_answer_material(text + " " + url)
                
                # Формируем путь: downloads/МГУ/Философия/2024/файл.pdf
                filename = normalize_filename(
                    text or Path(urlparse(url).path).name,
                    Path(urlparse(url).path).suffix,
                    url
                )
                
                dest_path = downloads_dir / org_name / subject / year / filename
                
                # Избегаем дубликатов имён
                counter = 2
                while dest_path.exists():
                    stem = dest_path.stem
                    dest_path = dest_path.with_name(f"{stem}_{counter}{dest_path.suffix}")
                    counter += 1
                
                logger.info(f"\n📄 {org_name} | {subject} | {year}")
                logger.info(f"   {text[:80]}")
                logger.info(f"   → {dest_path.relative_to(base_dir)}")
                
                if args.dry:
                    logger.info("   [DRY RUN] Файл не скачан")
                    continue
                
                # Скачиваем
                if download_file(url, dest_path, logger):
                    # Сохраняем в базу
                    db.add_file(url, {
                        "url": url,
                        "filename": filename,
                        "organizer": org_name,
                        "subject": subject,
                        "year": year,
                        "has_answers": has_answers,
                        "path": str(dest_path.relative_to(base_dir)),
                        "source_page": link_info["page_url"]
                    })
                    db.update_stats(org_name, subject)
                    db.save()
                    total_downloaded += 1
                    time.sleep(1)  # Пауза между скачиваниями
        
        # Итоговая статистика
        logger.info("\n" + "="*60)
        logger.info("ИТОГИ")
        logger.info("="*60)
        logger.info(f"Найдено файлов: {total_found}")
        logger.info(f"Скачано: {total_downloaded}")
        logger.info(f"Пропущено (уже есть): {total_skipped}")
        
        logger.info("\nСтатистика по организаторам:")
        stats = db.get_stats()
        for key, count in sorted(stats.items(), key=lambda x: -x[1]):
            logger.info(f"  {key.replace('_', ' ')}: {count}")
        
        logger.info("\n✅ ГОТОВО!")
        
    finally:
        if driver:
            driver.quit()
            logger.info("Selenium драйвер закрыт")

if __name__ == "__main__":
    main()
