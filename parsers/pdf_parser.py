"""
Улучшенный парсер PDF с поддержкой различных форматов олимпиад
Объединяет несколько подходов для максимального качества извлечения
"""
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import fitz  # PyMuPDF


class PDFParser:
    """Универсальный парсер для олимпиадных PDF"""

    # Паттерны для поиска вопросов
    QUESTION_PATTERNS = [
        r"Вопрос\s*(\d+)",
        r"Задание\s*(\d+)",
        r"Задача\s*(\d+)",
        r"№\s*(\d+)",
        r"^\s*(\d+)\.\s+",  # Просто номер с точкой в начале строки
    ]

    # Паттерны для баллов/очков
    SCORE_PATTERNS = [
        r"Балл(?:ы|ов)?:?\s*[-–—]?\s*([\d]+(?:[.,]\d+)?)",
        r"Оценка:?\s*[-–—]?\s*([\d]+(?:[.,]\d+)?)",
        r"\((\d+)\s*балл",
        r"(\d+)\s*(?:балл|очк|point)"
    ]

    # Паттерны для правильных ответов
    ANSWER_PATTERNS = [
        r"Правильн(?:ый|ые|ых)\s+ответ[ы]?:?\s*(.+?)(?=\n\s*(?:Вопрос|Задани|$))",
        r"Ответ:?\s*(.+?)(?=\n\s*(?:Вопрос|Задани|$))",
        r"Верн(?:ый|ые|ых)\s+ответ[ы]?:?\s*(.+?)(?=\n\s*(?:Вопрос|Задани|$))",
        r"Ключ:?\s*(.+?)(?=\n\s*(?:Вопрос|Задани|$))",
    ]

    # Слова-мусор для удаления
    NOISE_PATTERNS = [
        r"Размер\s+шрифта",
        r"Цвет\s+сайта",
        r"https?://\S+",
        r"javascript:void\(\S*\)",
        r"Page\s*\d+",
        r"Страница\s*\d+",
        r"©.*?\d{4}",
    ]

    def __init__(self):
        self.compiled_patterns = {
            'questions': [re.compile(p, re.MULTILINE) for p in self.QUESTION_PATTERNS],
            'scores': [re.compile(p, re.IGNORECASE) for p in self.SCORE_PATTERNS],
            'answers': [re.compile(p, re.IGNORECASE | re.DOTALL) for p in self.ANSWER_PATTERNS],
        }

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Извлечь текст из PDF"""
        text_parts = []

        with fitz.open(pdf_path) as doc:
            for page in doc:
                text = page.get_text("text")
                text_parts.append(text)

        return "\n".join(text_parts)

    def clean_text(self, text: str) -> str:
        """Очистить текст от шума"""
        # Убираем мусорные паттерны
        for pattern in self.NOISE_PATTERNS:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)

        # Нормализуем переносы строк
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Убираем лишние пробелы
        text = re.sub(r" {2,}", " ", text)

        return text.strip()

    def detect_question_type(self, block: str) -> str:
        """Определить тип вопроса"""
        block_lower = block.lower()

        # Проверяем на соответствие
        if any(word in block_lower for word in ["соответств", "установите соответствие", "сопоставьте"]):
            return "matching"

        # Проверяем на множественный выбор
        if "выберите все" in block_lower or "несколько правильных" in block_lower:
            return "multiple_choice"

        # Проверяем на открытый вопрос
        if "краткий ответ" in block_lower or "запишите ответ" in block_lower:
            return "text"

        # По умолчанию - одиночный выбор
        return "choice"

    def extract_question_number(self, block: str) -> Optional[str]:
        """Извлечь номер вопроса"""
        for pattern in self.compiled_patterns['questions']:
            match = pattern.search(block)
            if match:
                return match.group(1)
        return None

    def extract_score(self, block: str) -> float:
        """Извлечь баллы за вопрос"""
        for pattern in self.compiled_patterns['scores']:
            match = pattern.search(block)
            if match:
                score_str = match.group(1).replace(',', '.')
                try:
                    return float(score_str)
                except ValueError:
                    continue
        return 1.0  # Дефолтный балл

    def extract_question_text(self, block: str, after_marker: str = None) -> str:
        """
        Извлечь текст вопроса из блока

        Args:
            block: Текст блока
            after_marker: Начинать извлечение после этой строки
        """
        # Если указан маркер, начинаем после него
        if after_marker:
            parts = block.split(after_marker, 1)
            if len(parts) > 1:
                block = parts[1]

        # Убираем балл в начале
        block = re.sub(r'^[:\-–—\s]*\d+[.,]?\d*\s*', '', block, flags=re.MULTILINE)

        # Извлекаем до вариантов ответов или до конца
        cutoff_match = re.search(
            r'(?:Выберите|^\s*\d+[\.\)]|\n\s*[А-Я]\)|Правильн|Ответ:|Верн)',
            block,
            flags=re.MULTILINE | re.IGNORECASE
        )

        if cutoff_match:
            question_text = block[:cutoff_match.start()]
        else:
            # Берём первые несколько строк
            lines = block.split('\n')
            question_text = '\n'.join(lines[:5])

        # Очищаем
        question_text = self.clean_text(question_text)

        return question_text.strip()

    def extract_options(self, block: str) -> List[Dict[str, any]]:
        """
        Извлечь варианты ответов

        Returns:
            List of {"text": "...", "is_correct": False}
        """
        options = []

        # Паттерн для нумерованных вариантов: 1) ... или 1. ...
        option_pattern = re.compile(
            r'^\s*(\d+)[\.\)]\s*(.+?)(?=(?:\n\s*\d+[\.\)]|\n\s*Правильн|\n\s*Ответ:|\Z))',
            flags=re.MULTILINE | re.DOTALL
        )

        for match in option_pattern.finditer(block):
            option_text = match.group(2)
            # Убираем лишние переносы строк внутри варианта
            option_text = re.sub(r'\n+', ' ', option_text)
            option_text = self.clean_text(option_text)

            if option_text and len(option_text) > 1:
                options.append({
                    "text": option_text,
                    "is_correct": False  # Будет проставлено позже
                })

        # Если не нашли нумерованные, пробуем буквенные А) Б) В)
        if not options:
            letter_pattern = re.compile(
                r'^\s*([А-Я])\)\s*(.+?)(?=(?:\n\s*[А-Я]\)|\n\s*Правильн|\n\s*Ответ:|\Z))',
                flags=re.MULTILINE | re.DOTALL
            )

            for match in letter_pattern.finditer(block):
                option_text = match.group(2)
                option_text = re.sub(r'\n+', ' ', option_text)
                option_text = self.clean_text(option_text)

                if option_text and len(option_text) > 1:
                    options.append({
                        "text": option_text,
                        "is_correct": False
                    })

        return options

    def extract_correct_answers(self, block: str) -> List[str]:
        """Извлечь правильные ответы"""
        for pattern in self.compiled_patterns['answers']:
            match = pattern.search(block)
            if match:
                answer_text = match.group(1).strip()

                # Разделяем по разделителям
                answers = re.split(r'[;,\n]+', answer_text)
                answers = [self.clean_text(ans) for ans in answers if ans.strip()]

                return answers

        return []

    def mark_correct_options(self, options: List[Dict], correct_answers: List[str]) -> List[Dict]:
        """
        Отметить правильные варианты ответов

        Если correct_answers содержат номера, маркируем по индексу
        Иначе ищем совпадения по тексту
        """
        if not correct_answers:
            return options

        # Проверяем, являются ли ответы номерами
        if all(ans.isdigit() for ans in correct_answers):
            # Ответы в виде номеров
            correct_indices = [int(ans) - 1 for ans in correct_answers]
            for i, option in enumerate(options):
                option['is_correct'] = i in correct_indices
        else:
            # Ответы в виде текста - ищем совпадения
            for option in options:
                for correct_ans in correct_answers:
                    if correct_ans.lower() in option['text'].lower():
                        option['is_correct'] = True
                        break

        return options

    def parse_pdf(self, pdf_path: str, university: str = None, subject: str = None, year: str = None) -> List[Dict]:
        """
        Парсить PDF и извлечь вопросы

        Args:
            pdf_path: Путь к PDF файлу
            university: Название университета (для тегов)
            subject: Предмет (для тегов)
            year: Год (для тегов)

        Returns:
            Список вопросов в формате для DatabaseManager
        """
        print(f"📄 Парсинг: {pdf_path}")

        # Извлекаем текст
        text = self.extract_text_from_pdf(pdf_path)
        text = self.clean_text(text)

        # Разбиваем на блоки по вопросам
        blocks = self._split_into_question_blocks(text)

        print(f"   Найдено блоков: {len(blocks)}")

        questions = []

        for block in blocks:
            try:
                question = self._parse_question_block(block, pdf_path, university, subject, year)
                if question:
                    questions.append(question)
            except Exception as e:
                print(f"   ⚠ Ошибка парсинга блока: {e}")
                continue

        print(f"   ✓ Извлечено вопросов: {len(questions)}")

        return questions

    def _split_into_question_blocks(self, text: str) -> List[str]:
        """Разбить текст на блоки по вопросам"""
        # Пробуем найти маркеры вопросов
        all_matches = []

        for pattern in self.compiled_patterns['questions']:
            for match in pattern.finditer(text):
                all_matches.append(match.start())

        if not all_matches:
            # Если не нашли маркеров, возвращаем весь текст
            return [text]

        # Сортируем позиции
        all_matches = sorted(set(all_matches))

        # Разбиваем на блоки
        blocks = []
        for i in range(len(all_matches)):
            start = all_matches[i]
            end = all_matches[i + 1] if i + 1 < len(all_matches) else len(text)
            blocks.append(text[start:end])

        return blocks

    def _parse_question_block(
        self,
        block: str,
        pdf_path: str,
        university: str = None,
        subject: str = None,
        year: str = None
    ) -> Optional[Dict]:
        """Парсить один блок вопроса"""

        # Извлекаем компоненты
        question_num = self.extract_question_number(block)
        question_type = self.detect_question_type(block)
        score = self.extract_score(block)
        question_text = self.extract_question_text(block)
        options = self.extract_options(block) if question_type in ['choice', 'multiple_choice'] else []
        correct_answers = self.extract_correct_answers(block)

        # Маркируем правильные ответы
        if options and correct_answers:
            options = self.mark_correct_options(options, correct_answers)

        # Фильтруем слишком короткие вопросы
        if not question_text or len(question_text) < 10:
            return None

        # Формируем объект вопроса
        question_obj = {
            "text": question_text,
            "type": question_type,
            "points": score,
            "options": options,
            "source_pdf": str(pdf_path),
            "tags": {}
        }

        # Добавляем теги
        if university:
            question_obj["tags"]["university"] = [university]
        if subject:
            question_obj["tags"]["subject"] = [subject]
        if year:
            question_obj["tags"]["year"] = [year]

        return question_obj


if __name__ == "__main__":
    # Тестирование на примере файла
    parser = PDFParser()

    # Если есть тестовый PDF
    test_pdf = Path("../chatGPT/23219856-ans-soci-10-otbor-21-22.pdf")

    if test_pdf.exists():
        questions = parser.parse_pdf(
            str(test_pdf),
            university="ВШЭ",
            subject="Обществознание",
            year="2021"
        )

        print(f"\n✅ Всего извлечено: {len(questions)} вопросов")

        if questions:
            print("\n📝 Пример первого вопроса:")
            q = questions[0]
            print(f"  Текст: {q['text'][:150]}...")
            print(f"  Тип: {q['type']}")
            print(f"  Баллы: {q['points']}")
            print(f"  Вариантов: {len(q['options'])}")
            if q['options']:
                print(f"  Первый вариант: {q['options'][0]['text'][:80]}...")
    else:
        print(f"⚠ Тестовый файл не найден: {test_pdf}")
