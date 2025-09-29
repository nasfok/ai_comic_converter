import logging
import os
import json
import requests
from typing import Dict, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import openai

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentAnalyzer:
    """Анализатор документов для создания комиксов"""

    def analyze_document(self, document_text: str) -> Dict:
        """Анализирует документ и создает структуру для комикса"""
        try:
            # Парсим JSON если это JSON, иначе обрабатываем как plain text
            if document_text.strip().startswith('{'):
                data = json.loads(document_text)
                return self._process_json_structure(data)
            else:
                return self._process_plain_text(document_text)
        except json.JSONDecodeError:
            return self._process_plain_text(document_text)

    def _process_json_structure(self, data: Dict) -> Dict:
        """Обрабатывает структурированный JSON"""
        scenes = []

        if "panels" in data:
            # Обрабатываем готовую структуру панелей
            for i, panel_data in enumerate(data["panels"]):
                scene = {
                    "title": f"Panel {panel_data.get('panel_number', i + 1)}",
                    "description": panel_data.get("visual_description", ""),
                    "visual_elements": self._extract_visual_elements(panel_data.get("visual_description", "")),
                    "is_climax": i == len(data["panels"]) // 2,
                    "mood": "professional"
                }
                scenes.append(scene)

        return {
            "title": data.get("script_title", "Generated Comic"),
            "scenes": scenes,
            "characters": [{
                "name": "Main Character",
                "description": "Primary character from the document",
                "visual_appearance": "professional, modern clothing",
                "personality": "intelligent, determined"
            }],
            "style": "graphic_novel",
            "target_format": "web_comic"
        }

    def _process_plain_text(self, text: str) -> Dict:
        """Обрабатывает обычный текст"""
        paragraphs = [p.strip() for p in text.split('\n') if p.strip() and len(p.strip()) > 10]

        scenes = []
        for i, paragraph in enumerate(paragraphs[:6]):  # Максимум 6 сцен
            scenes.append({
                "title": f"Scene {i + 1}",
                "description": paragraph,
                "visual_elements": self._extract_visual_elements(paragraph),
                "is_climax": i == len(paragraphs) // 2,
                "mood": self._detect_mood(paragraph)
            })

        return {
            "title": "Document Comic",
            "scenes": scenes,
            "characters": [{
                "name": "Document Reader",
                "description": "Person engaging with the document content",
                "visual_appearance": "professional, thoughtful expression",
                "personality": "curious, analytical"
            }],
            "style": "graphic_novel",
            "target_format": "web_comic"
        }

    def _extract_visual_elements(self, text: str) -> List[str]:
        """Извлекает визуальные элементы из текста"""
        elements = []
        text_lower = text.lower()

        if any(word in text_lower for word in ["waterfall", "nature", "trees", "greenery"]):
            elements.extend(["nature", "landscape", "outdoors"])
        if any(word in text_lower for word in ["laptop", "computer", "github", "code"]):
            elements.extend(["technology", "computer", "coding"])
        if any(word in text_lower for word in ["school", "lyceum", "education"]):
            elements.extend(["education", "school", "learning"])
        if any(word in text_lower for word in ["olympiad", "competition", "achievement"]):
            elements.extend(["achievement", "competition", "success"])

            return elements if elements else ["general", "conversation"]

        def _detect_mood(self, text: str) -> str:
            """Определяет настроение текста"""
            text_lower = text.lower()

            if any(word in text_lower for word in ["achievement", "success", "win", "gold"]):
                return "triumphant"
            elif any(word in text_lower for word in ["education", "learning", "study"]):
                return "focused"
            elif any(word in text_lower for word in ["technology", "code", "development"]):
                return "technical"
            else:
                return "neutral"

    class Dalle3Generator:
        """Генератор изображений через DALL-E 3"""

        def __init__(self, api_key: str):
            self.client = openai.OpenAI(api_key=api_key)
            self.output_dir = Path("comic_output")
            self.output_dir.mkdir(exist_ok=True)

        def generate_image(self, prompt: str, panel_id: int) -> Optional[Path]:
            """Генерирует изображение через DALL-E 3"""
            try:
                response = self.client.images.generate(
                    model="dall-e-3",
                    prompt=prompt[:4000],
                    size="1024x1024",
                    quality="standard",
                    n=1,
                )

                image_url = response.data[0].url
                image_response = requests.get(image_url)

                if image_response.status_code == 200:
                    image_path = self.output_dir / f"panel_{panel_id:03d}.png"
                    with open(image_path, 'wb') as f:
                        f.write(image_response.content)
                    return image_path

            except Exception as e:
                logger.error(f"DALL-E 3 generation failed: {e}")

            return None


class PromptEngine:
    """Движок для создания промптов"""

    def generate_panel_prompt(self, scene: Dict, character: Dict, panel_number: int) -> str:
        """Создает промпт для генерации изображения панели"""

        base_prompt = (
            "Create a detailed comic book panel illustration in graphic novel style. "
            "Professional artwork, clear storytelling, dynamic composition. "
            "High quality, detailed, vibrant colors."
        )

        # Описание сцены
        scene_desc = f"The scene shows: {scene['description']}"

        # Визуальные элементы
        visual_elements = ""
        if scene['visual_elements']:
            visual_elements = f"Key visual elements: {', '.join(scene['visual_elements'])}."

        # Описание персонажа
        character_desc = (
            f"The main character is {character['name']}: {character['description']}, "
            f"appearing as {character['visual_appearance']} with {character['personality']} personality."
        )

        # Специальные инструкции для кульминации
        climax_emphasis = ""
        if scene['is_climax']:
            climax_emphasis = "This is a climactic moment - make it dramatic and impactful with dynamic lighting and composition."

        # Стилевые указания
        style_guide = (
            "Style: Western graphic novel, clear line work, professional coloring, "
            "balanced composition suitable for comic book publication."
        )

        prompt_parts = [
            base_prompt,
            scene_desc,
            visual_elements,
            character_desc,
            climax_emphasis,
            style_guide
        ]

        # Убираем пустые части и объединяем
        clean_parts = [part for part in prompt_parts if part]
        return " ".join(clean_parts)


class LayoutPlanner:
    """Планировщик макетов страниц комикса"""

    def __init__(self):
        self.page_width = 1200
        self.page_height = 1800

    def create_page_layouts(self, scenes: List[Dict]) -> List[Dict]:
        """Создает макеты страниц из сцен"""
        pages = []
        panels_per_page = 4

        for page_num, page_start in enumerate(range(0, len(scenes), panels_per_page)):
            page_scenes = scenes[page_start:page_start + panels_per_page]
            page_layout = self._create_single_page(page_scenes, page_num + 1)
            pages.append(page_layout)

        return pages

    def _create_single_page(self, scenes: List[Dict], page_number: int) -> Dict:
        """Создает макет одной страницы"""
        layout_templates = {
            1: [{"x": 0.1, "y": 0.1, "width": 0.8, "height": 0.8}],
            2: [
                {"x": 0.1, "y": 0.1, "width": 0.8, "height": 0.4},
                {"x": 0.1, "y": 0.5, "width": 0.8, "height": 0.4}
            ],
            3: [
                {"x": 0.1, "y": 0.1, "width": 0.8, "height": 0.25},
                {"x": 0.1, "y": 0.4, "width": 0.8, "height": 0.25},
                {"x": 0.1, "y": 0.7, "width": 0.8, "height": 0.25}
            ],
            4: [
                {"x": 0.05, "y": 0.05, "width": 0.45, "height": 0.45},
                {"x": 0.55, "y": 0.05, "width": 0.4, "height": 0.45},
                {"x": 0.05, "y": 0.55, "width": 0.45, "height": 0.4},
                {"x": 0.55, "y": 0.55, "width": 0.4, "height": 0.4}
            ]
        }

        template = layout_templates.get(len(scenes), layout_templates[1])
        panels = []

        for i, (scene, pos) in enumerate(zip(scenes, template)):
            panel_id = (page_number - 1) * 4 + i + 1
            panels.append({
                "panel_id": panel_id,
                "scene": scene,
                "position": pos,
                "image_generated": False,
                "image_path": None
            })

        return {
            "page_number": page_number,
            "panels": panels,
            "width": self.page_width,
            "height": self.page_height
        }


class ComicGenerator:
    """Основной генератор комиксов"""

    def __init__(self, openai_api_key: str):
        self.document_analyzer = DocumentAnalyzer()
        self.layout_planner = LayoutPlanner()
        self.prompt_engine = PromptEngine()
        self.image_generator = Dalle3Generator(openai_api_key)

    def generate_comic(self, document_text: str) -> Dict:
        """Генерирует полный комикс из документа"""
        logger.info("Starting comic generation...")

        # Шаг 1: Анализ документа
        comic_data = self.document_analyzer.analyze_document(document_text)
        logger.info(f"Document analyzed: {len(comic_data['scenes'])} scenes found")

        # Шаг 2: Создание макетов страниц
        pages = self.layout_planner.create_page_layouts(comic_data["scenes"])
        logger.info(f"Layout created: {len(pages)} pages")

        # Шаг 3: Генерация изображений
        main_character = comic_data["characters"][0]
        generated_panels = 0

        for page in pages:
            for panel in page["panels"]:
                prompt = self.prompt_engine.generate_panel_prompt(
                    panel["scene"], main_character, panel["panel_id"]
                )

                image_path = self.image_generator.generate_image(prompt, panel["panel_id"])

                if image_path:
                    panel["image_path"] = str(image_path)
                    panel["image_generated"] = True
                    panel["generation_method"] = "dalle3"
                    generated_panels += 1
                    logger.info(f"Generated panel {panel['panel_id']}")
                else:
                    # Создаем fallback изображение
                    fallback_path = self._create_fallback_image(panel["panel_id"], panel["scene"]["description"])
                    panel["image_path"] = str(fallback_path)
                    panel["image_generated"] = True
                    panel["generation_method"] = "fallback"
                    logger.warning(f"Used fallback for panel {panel['panel_id']}")

        # Шаг 4: Компоновка результатов
        result = {
            "title": comic_data["title"],
            "metadata": {
                "total_pages": len(pages),
                "total_panels": sum(len(page["panels"]) for page in pages),
                "generated_panels": generated_panels,
                "success_rate": f"{(generated_panels / sum(len(page['panels']) for page in pages)) * 100:.1f}%"
            },
            "pages": pages,
            "characters": comic_data["characters"]
        }

        logger.info("Comic generation completed successfully!")
        return result

    def _create_fallback_image(self, panel_id: int, description: str) -> Path:
        """Создает резервное изображение когда DALL-E 3 недоступен"""
        width, height = 1024, 1024
        image = Image.new('RGB', (width, height), color='#f0f8ff')  # Alice blue background
        draw = ImageDraw.Draw(image)

        # Рамка
        draw.rectangle([10, 10, width - 10, height - 10], outline='#2c3e50', width=4)

        try:
            # Заголовок
            font_large = ImageFont.truetype("arial.ttf", 36)
            font_small = ImageFont.truetype("arial.ttf", 24)

            title = f"COMIC PANEL {panel_id}"
            title_bbox = draw.textbbox((0, 0), title, font=font_large)
            title_width = title_bbox[2] - title_bbox[0]
            draw.text(((width - title_width) // 2, 50), title, fill='#2c3e50', font=font_large)

            # Описание
            words = description.split()
            lines = []
            current_line = []

            for word in words:
                test_line = ' '.join(current_line + [word])
                bbox = draw.textbbox((0, 0), test_line, font=font_small)
                if bbox[2] < width - 100:
                    current_line.append(word)
                else:
                    lines.append(' '.join(current_line))

                    current_line = [word]

            if current_line:
                lines.append(' '.join(current_line))

            # Ограничиваем количество строк
            lines = lines[:5]

            for i, line in enumerate(lines):
                bbox = draw.textbbox((0, 0), line, font=font_small)
                line_width = bbox[2] - bbox[0]
                y_pos = 150 + i * 40
                draw.text(((width - line_width) // 2, y_pos), line, fill='#34495e', font=font_small)

            # Декоративный элемент
            draw.rectangle([width // 4, height // 2, 3 * width // 4, 3 * height // 4],
                           fill='#ecf0f1', outline='#bdc3c7', width=2)

        except Exception as e:
            logger.warning(f"Could not add text to fallback image: {e}")

        output_path = self.image_generator.output_dir / f"fallback_{panel_id:03d}.png"
        image.save(output_path)
        return output_path

    def save_comic_report(self, comic_data: Dict, output_path: str = "comic_report.json"):
        """Сохраняет отчет о генерации комикса"""
        report = {
            "title": comic_data["title"],
            "summary": comic_data["metadata"],
            "pages": []
        }

        for page in comic_data["pages"]:
            page_report = {
                "page_number": page["page_number"],
                "panels": []
            }

            for panel in page["panels"]:
                panel_report = {
                    "panel_id": panel["panel_id"],
                    "scene_description": panel["scene"]["description"],
                    "image_generated": panel["image_generated"],
                    "generation_method": panel.get("generation_method", "unknown"),
                    "image_path": panel.get("image_path")
                }
                page_report["panels"].append(panel_report)

            report["pages"].append(page_report)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"Comic report saved to {output_path}")


def main():
    """Пример использования генератора комиксов"""

    # Проверяем API ключ
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ ERROR: Please set OPENAI_API_KEY environment variable")
        print("Example: export OPENAI_API_KEY='your-api-key-here'")
        return

    # Тестовый документ (может быть любым текстом или JSON)
    test_document = """
{
  "script_title": "Биография Олега Дроканова",
  "panels": [
    {
      "panel_number": 1,
      "visual_description": "Молодой человек стоит у водопада в природной зоне, улыбается и держит ноутбук. На заднем плане красивые деревья и зелень.",
      "dialogue_text": ""
    },
    {
      "panel_number": 2, 
      "visual_description": "Экран ноутбука показывает GitHub профиль с проектами и достижениями в области программирования и искусственного интеллекта.",
      "dialogue_text": ""
    },
    {
      "panel_number": 3,
      "visual_description": "Студент стоит перед зданием Президентского физико-математического лицея №239, выглядит сосредоточенным и целеустремленным.",
      "dialogue_text": ""
    },
    {
      "panel_number": 4,
      "visual_description": "Церемония награждения на международной олимпиаде, молодой человек получает золотую медаль за достижения в искусственном интеллекте.",
      "dialogue_text": ""
    }
  ]
}
"""

    print("🎨 Starting Comic Generation...")
    print("This may take a few minutes...")

    # Создаем генератор
    generator = ComicGenerator(api_key)

    # Генерируем комикс
    comic = generator.generate_comic(test_document)

    # Сохраняем отчет
    generator.save_comic_report(comic)

    # Выводим результаты
    print(f"\n✅ COMIC GENERATION COMPLETE!")
    print(f"📖 Title: {comic['title']}")
    print(f"📄 Pages: {comic['metadata']['total_pages']}")
    print(f"🖼  Panels: {comic['metadata']['total_panels']} (Generated: {comic['metadata']['generated_panels']})")
    print(f"📊 Success Rate: {comic['metadata']['success_rate']}")

    print(f"\n📁 Generated files are in: comic_output/")
    print(f"📋 Report saved to: comic_report.json")

    # Показываем детали по страницам
    print(f"\n📄 PAGE DETAILS:")
    for page in comic['pages']:
        print(f"  Page {page['page_number']}:")
        for panel in page['panels']:
            status = "✅" if panel['image_generated'] else "❌"
            method = panel.get('generation_method', 'unknown')
            print(f"    Panel {panel['panel_id']}: {status} ({method})")


if __name__ == "__main__":
    main()
