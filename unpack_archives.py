#!/usr/bin/env python3
"""
Скрипт для распаковки всех ZIP архивов и удаления их после распаковки
"""
import os
import zipfile
from pathlib import Path
import shutil
import argparse


def unpack_archive(zip_path: Path, delete_after: bool = True):
    """
    Распаковать один ZIP архив

    Args:
        zip_path: путь к ZIP файлу
        delete_after: удалить архив после распаковки
    """
    # Папка для распаковки - та же директория, где лежит архив
    extract_dir = zip_path.parent

    try:
        print(f"📦 Распаковка: {zip_path}")

        # Распаковываем
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Получаем список файлов в архиве
            file_list = zip_ref.namelist()
            pdf_count = sum(1 for f in file_list if f.lower().endswith('.pdf'))

            print(f"   Файлов в архиве: {len(file_list)} (PDF: {pdf_count})")

            # Распаковываем все файлы
            zip_ref.extractall(extract_dir)

        print(f"   ✓ Распаковано в: {extract_dir}")

        # Удаляем архив если требуется
        if delete_after:
            zip_path.unlink()
            print(f"   ✓ Архив удалён")

        return True, pdf_count

    except Exception as e:
        print(f"   ✗ Ошибка: {e}")
        return False, 0


def find_all_archives(root_dir: Path, pattern: str = "**/*.zip"):
    """Найти все ZIP архивы"""
    archives = list(root_dir.glob(pattern))
    return sorted(archives)


def main():
    parser = argparse.ArgumentParser(description="Распаковка ZIP архивов")
    parser.add_argument(
        "directory",
        nargs="?",
        default="olympiads/downloads",
        help="Директория для поиска архивов (по умолчанию: olympiads/downloads)"
    )
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Не удалять архивы после распаковки"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Только показать что будет сделано"
    )

    args = parser.parse_args()

    root_dir = Path(args.directory)

    if not root_dir.exists():
        print(f"❌ Директория не найдена: {root_dir}")
        return

    print(f"🔍 Поиск ZIP архивов в: {root_dir}")
    archives = find_all_archives(root_dir)

    if not archives:
        print("✓ ZIP архивов не найдено")
        return

    print(f"📦 Найдено архивов: {len(archives)}")
    print()

    if args.dry_run:
        print("🔍 Режим предварительного просмотра (--dry-run)")
        print()
        for archive in archives:
            print(f"  • {archive}")
        print()
        print(f"Для распаковки запустите без --dry-run")
        return

    # Статистика
    total_archives = len(archives)
    successful = 0
    failed = 0
    total_pdfs = 0

    # Распаковываем
    for i, archive in enumerate(archives, 1):
        print(f"\n[{i}/{total_archives}]")
        success, pdf_count = unpack_archive(
            archive,
            delete_after=not args.keep
        )

        if success:
            successful += 1
            total_pdfs += pdf_count
        else:
            failed += 1

    # Итоговая статистика
    print()
    print("=" * 60)
    print("📊 ИТОГИ")
    print("=" * 60)
    print(f"Всего архивов: {total_archives}")
    print(f"Успешно распаковано: {successful}")
    print(f"Ошибок: {failed}")
    print(f"Извлечено PDF файлов: {total_pdfs}")

    if not args.keep:
        print(f"Архивы удалены: {successful}")
    else:
        print(f"Архивы сохранены (--keep)")

    print()
    print("✅ Готово!")


if __name__ == "__main__":
    main()
