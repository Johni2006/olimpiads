#!/usr/bin/env python3
"""
Скрипт для массового импорта PDF в базу данных
Обходит папку downloads и парсит все найденные PDF
"""
import sys
import json
from pathlib import Path
from typing import List, Dict
import argparse

# Добавляем пути к модулям
sys.path.insert(0, str(Path(__file__).parent))

from database.db_manager import DatabaseManager
from parsers.pdf_parser import PDFParser
from parsers.image_extractor import ImageExtractor


class PDFImporter:
    """Импортер PDF файлов в базу данных"""

    def __init__(
        self,
        db_path: str = "olympiad_questions.db",
        images_dir: str = "question_images"
    ):
        self.db = DatabaseManager(db_path)
        self.parser = PDFParser()
        self.image_extractor = ImageExtractor(output_dir=images_dir)

        self.stats = {
            "total_pdfs": 0,
            "successful_pdfs": 0,
            "total_questions": 0,
            "total_images": 0,
            "errors": []
        }

    def extract_metadata_from_path(self, pdf_path: Path) -> Dict[str, str]:
        """
        Извлечь метаданные из пути к файлу
        Структура: downloads/Университет/Предмет/Год/файл.pdf
        """
        parts = pdf_path.parts

        metadata = {
            "university": None,
            "subject": None,
            "year": None
        }

        # Пытаемся извлечь из структуры папок
        try:
            # Находим индекс папки "downloads"
            if "downloads" in parts:
                downloads_idx = parts.index("downloads")

                # После downloads идут: университет/предмет/год
                if len(parts) > downloads_idx + 1:
                    metadata["university"] = parts[downloads_idx + 1]

                if len(parts) > downloads_idx + 2:
                    metadata["subject"] = parts[downloads_idx + 2]

                if len(parts) > downloads_idx + 3:
                    year = parts[downloads_idx + 3]
                    # Проверяем, что это действительно год
                    if year.isdigit() and len(year) == 4:
                        metadata["year"] = year

        except Exception as e:
            print(f"   ⚠ Ошибка извлечения метаданных из пути: {e}")

        # Дополнительно пытаемся извлечь из имени файла
        filename = pdf_path.stem.lower()

        # Год из имени файла
        import re
        year_match = re.search(r'20\d{2}', filename)
        if year_match and not metadata["year"]:
            metadata["year"] = year_match.group(0)

        return metadata

    def import_single_pdf(
        self,
        pdf_path: Path,
        extract_images: bool = True,
        force: bool = False
    ) -> int:
        """
        Импортировать один PDF файл

        Returns:
            Количество импортированных вопросов
        """
        print(f"\n{'='*70}")
        print(f"📄 Импорт: {pdf_path.relative_to(Path.cwd()) if pdf_path.is_relative_to(Path.cwd()) else pdf_path}")
        print(f"{'='*70}")

        self.stats["total_pdfs"] += 1

        # Извлекаем метаданные из пути
        metadata = self.extract_metadata_from_path(pdf_path)
        print(f"📋 Метаданные:")
        print(f"   Университет: {metadata['university'] or 'не определён'}")
        print(f"   Предмет: {metadata['subject'] or 'не определён'}")
        print(f"   Год: {metadata['year'] or 'не определён'}")

        try:
            # Парсим PDF
            questions = self.parser.parse_pdf(
                str(pdf_path),
                university=metadata["university"],
                subject=metadata["subject"],
                year=metadata["year"]
            )

            if not questions:
                print("   ⚠ Вопросы не найдены")
                return 0

            # Извлекаем изображения, если требуется
            images_by_page = {}
            if extract_images:
                try:
                    images_by_page = self.image_extractor.extract_images_by_page(str(pdf_path))
                    total_images = sum(len(imgs) for imgs in images_by_page.values())
                    self.stats["total_images"] += total_images
                except Exception as e:
                    print(f"   ⚠ Ошибка извлечения изображений: {e}")

            # Импортируем вопросы в БД
            imported_count = 0
            for question_data in questions:
                try:
                    question_id = self.db.add_question(
                        text=question_data["text"],
                        question_type=question_data["type"],
                        options=question_data.get("options"),
                        tags=question_data.get("tags"),
                        points=question_data.get("points", 1.0),
                        source_pdf=str(pdf_path)
                    )

                    imported_count += 1

                    # TODO: Связать изображения с вопросом
                    # Для этого нужно определить, на какой странице находится вопрос

                except Exception as e:
                    print(f"   ⚠ Ошибка импорта вопроса: {e}")
                    self.stats["errors"].append(f"{pdf_path.name}: {str(e)}")
                    continue

            self.stats["total_questions"] += imported_count
            self.stats["successful_pdfs"] += 1

            print(f"✅ Импортировано вопросов: {imported_count}")
            return imported_count

        except Exception as e:
            print(f"❌ Ошибка импорта PDF: {e}")
            self.stats["errors"].append(f"{pdf_path.name}: {str(e)}")
            return 0

    def import_directory(
        self,
        directory: Path,
        pattern: str = "**/*.pdf",
        extract_images: bool = True,
        limit: int = None
    ):
        """
        Импортировать все PDF из директории

        Args:
            directory: Путь к директории
            pattern: Паттерн поиска файлов
            extract_images: Извлекать ли изображения
            limit: Максимальное количество PDF для импорта (None = все)
        """
        print(f"\n🔍 Поиск PDF файлов в: {directory}")
        print(f"   Паттерн: {pattern}")

        pdf_files = list(directory.glob(pattern))
        print(f"   Найдено файлов: {len(pdf_files)}")

        if limit:
            pdf_files = pdf_files[:limit]
            print(f"   Обрабатываем первые: {limit}")

        for pdf_path in pdf_files:
            self.import_single_pdf(pdf_path, extract_images=extract_images)

    def print_stats(self):
        """Вывести итоговую статистику"""
        print(f"\n{'='*70}")
        print("📊 СТАТИСТИКА ИМПОРТА")
        print(f"{'='*70}")
        print(f"PDF файлов обработано: {self.stats['total_pdfs']}")
        print(f"PDF успешно импортировано: {self.stats['successful_pdfs']}")
        print(f"Вопросов добавлено: {self.stats['total_questions']}")
        print(f"Изображений извлечено: {self.stats['total_images']}")

        if self.stats['errors']:
            print(f"\n⚠ Ошибок: {len(self.stats['errors'])}")
            for error in self.stats['errors'][:10]:  # Показываем первые 10
                print(f"   • {error}")
            if len(self.stats['errors']) > 10:
                print(f"   ... и ещё {len(self.stats['errors']) - 10}")

        # Статистика из БД
        print(f"\n📊 СТАТИСТИКА БАЗЫ ДАННЫХ")
        print(f"{'='*70}")

        db_stats = self.db.get_stats()
        print(f"Всего вопросов в БД: {db_stats['total_questions']}")

        if db_stats['by_subject']:
            print(f"\nПо предметам:")
            for subject, count in sorted(db_stats['by_subject'].items(), key=lambda x: -x[1]):
                print(f"   {subject}: {count}")

        if db_stats['by_university']:
            print(f"\nПо университетам:")
            for uni, count in sorted(db_stats['by_university'].items(), key=lambda x: -x[1]):
                print(f"   {uni}: {count}")


def main():
    parser = argparse.ArgumentParser(
        description="Импорт олимпиадных PDF в базу данных"
    )

    parser.add_argument(
        "input",
        help="Путь к PDF файлу или директории с PDF"
    )

    parser.add_argument(
        "--db",
        default="olympiad_questions.db",
        help="Путь к базе данных (по умолчанию: olympiad_questions.db)"
    )

    parser.add_argument(
        "--images-dir",
        default="question_images",
        help="Папка для сохранения изображений"
    )

    parser.add_argument(
        "--no-images",
        action="store_true",
        help="Не извлекать изображения"
    )

    parser.add_argument(
        "--pattern",
        default="**/*.pdf",
        help="Паттерн поиска PDF (для директорий)"
    )

    parser.add_argument(
        "--limit",
        type=int,
        help="Максимальное количество PDF для импорта"
    )

    args = parser.parse_args()

    # Создаём импортер
    importer = PDFImporter(
        db_path=args.db,
        images_dir=args.images_dir
    )

    # Определяем, что импортировать
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"❌ Путь не существует: {input_path}")
        sys.exit(1)

    if input_path.is_file() and input_path.suffix.lower() == '.pdf':
        # Один файл
        importer.import_single_pdf(
            input_path,
            extract_images=not args.no_images
        )
    elif input_path.is_dir():
        # Директория
        importer.import_directory(
            input_path,
            pattern=args.pattern,
            extract_images=not args.no_images,
            limit=args.limit
        )
    else:
        print(f"❌ Неверный путь: должен быть PDF файл или директория")
        sys.exit(1)

    # Выводим статистику
    importer.print_stats()


if __name__ == "__main__":
    main()
