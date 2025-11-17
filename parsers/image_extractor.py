"""
Модуль для извлечения изображений из PDF
Сохраняет графики, диаграммы, схемы из олимпиадных заданий
"""
import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Dict, Tuple
from PIL import Image
import io
import hashlib


class ImageExtractor:
    """Извлекает изображения из PDF и сохраняет их"""

    def __init__(self, output_dir: str = "extracted_images"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract_images_from_pdf(
        self,
        pdf_path: str,
        min_width: int = 100,
        min_height: int = 100
    ) -> List[Dict]:
        """
        Извлечь все изображения из PDF

        Args:
            pdf_path: Путь к PDF файлу
            min_width: Минимальная ширина изображения (фильтр мелких иконок)
            min_height: Минимальная высота изображения

        Returns:
            Список словарей с информацией об изображениях:
            [
                {
                    "page": 1,
                    "index": 0,
                    "file_path": "path/to/image.png",
                    "width": 800,
                    "height": 600,
                    "format": "png"
                },
                ...
            ]
        """
        pdf_path = Path(pdf_path)
        images_info = []

        print(f"🖼️  Извлечение изображений из: {pdf_path.name}")

        with fitz.open(pdf_path) as doc:
            for page_num, page in enumerate(doc, start=1):
                # Получаем список изображений на странице
                image_list = page.get_images(full=True)

                for img_index, img in enumerate(image_list):
                    try:
                        # Извлекаем изображение
                        xref = img[0]
                        base_image = doc.extract_image(xref)

                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]
                        width = base_image.get("width", 0)
                        height = base_image.get("height", 0)

                        # Фильтруем мелкие изображения (иконки, логотипы)
                        if width < min_width or height < min_height:
                            continue

                        # Создаём уникальное имя файла
                        image_hash = hashlib.md5(image_bytes).hexdigest()[:12]
                        filename = f"{pdf_path.stem}_p{page_num}_img{img_index}_{image_hash}.{image_ext}"
                        save_path = self.output_dir / filename

                        # Сохраняем изображение
                        with open(save_path, "wb") as img_file:
                            img_file.write(image_bytes)

                        # Добавляем информацию
                        images_info.append({
                            "page": page_num,
                            "index": img_index,
                            "file_path": str(save_path),
                            "width": width,
                            "height": height,
                            "format": image_ext,
                            "size_kb": len(image_bytes) / 1024
                        })

                        print(f"   ✓ Страница {page_num}, изображение {img_index}: {width}x{height} → {filename}")

                    except Exception as e:
                        print(f"   ⚠ Ошибка извлечения изображения на стр. {page_num}: {e}")
                        continue

        print(f"   Всего извлечено изображений: {len(images_info)}")
        return images_info

    def extract_images_by_page(self, pdf_path: str) -> Dict[int, List[Dict]]:
        """
        Извлечь изображения, сгруппированные по страницам

        Returns:
            {1: [img1, img2], 2: [img3], ...}
        """
        all_images = self.extract_images_from_pdf(pdf_path)

        images_by_page = {}
        for img_info in all_images:
            page = img_info["page"]
            if page not in images_by_page:
                images_by_page[page] = []
            images_by_page[page].append(img_info)

        return images_by_page

    def detect_image_type(self, image_path: str) -> str:
        """
        Определить тип изображения (график, схема, фото и т.д.)
        Простая эвристика на основе размера и формы

        Returns:
            'graph', 'diagram', 'photo', 'scheme', 'other'
        """
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                aspect_ratio = width / height

                # Эвристики
                if 1.5 < aspect_ratio < 2.5:
                    return "graph"  # Графики обычно широкие
                elif 0.8 < aspect_ratio < 1.2:
                    return "diagram"  # Квадратные - диаграммы
                elif width > 800 and height > 600:
                    return "photo"  # Большие - фотографии
                else:
                    return "scheme"  # Остальное - схемы

        except Exception:
            return "other"

    def resize_image_if_needed(
        self,
        image_path: str,
        max_width: int = 1200,
        max_height: int = 1200
    ) -> str:
        """
        Изменить размер изображения, если оно слишком большое
        (для оптимизации хранения и отображения)

        Returns:
            Путь к обработанному изображению
        """
        try:
            with Image.open(image_path) as img:
                width, height = img.size

                # Проверяем, нужно ли изменять размер
                if width <= max_width and height <= max_height:
                    return image_path

                # Вычисляем новые размеры с сохранением пропорций
                ratio = min(max_width / width, max_height / height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)

                # Изменяем размер
                resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

                # Сохраняем
                resized_path = Path(image_path).with_suffix(".resized" + Path(image_path).suffix)
                resized.save(resized_path, quality=90, optimize=True)

                print(f"   📐 Изменён размер: {width}x{height} → {new_width}x{new_height}")

                return str(resized_path)

        except Exception as e:
            print(f"   ⚠ Ошибка изменения размера: {e}")
            return image_path


if __name__ == "__main__":
    # Тестирование
    extractor = ImageExtractor(output_dir="test_images")

    # Тестовый PDF
    test_pdf = Path("../chatGPT/23219856-ans-soci-10-otbor-21-22.pdf")

    if test_pdf.exists():
        images = extractor.extract_images_from_pdf(str(test_pdf))

        print(f"\n✅ Всего извлечено: {len(images)} изображений")

        if images:
            print("\n📊 Примеры изображений:")
            for img in images[:3]:
                print(f"  • Страница {img['page']}: {img['width']}x{img['height']} px, {img['size_kb']:.1f} KB")
                print(f"    → {img['file_path']}")

                # Определяем тип
                img_type = extractor.detect_image_type(img['file_path'])
                print(f"    Тип: {img_type}")
    else:
        print(f"⚠ Тестовый файл не найден: {test_pdf}")
