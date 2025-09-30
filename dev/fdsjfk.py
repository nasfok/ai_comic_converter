import requests
import time
import os
from urllib.parse import urlparse

# Конфигурация
API_KEY = "gen-api key"
NETWORK_ID = "dalle-3"
API_BASE = "https://api.gen-api.ru/api/v1"
OUTPUT_FOLDER = "comic_images"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}


def save_image_from_url(image_url, filename):
    """Скачивает и сохраняет изображение по URL"""
    try:
        response = requests.get(image_url)
        response.raise_for_status()

        file_extension = ".png"
        full_filename = f"{filename}{file_extension}"
        filepath = os.path.join(OUTPUT_FOLDER, full_filename)

        with open(filepath, 'wb') as f:
            f.write(response.content)

        print(f"✅ Изображение сохранено: {filepath}")
        return filepath
    except Exception as e:
        print(f"❌ Ошибка при сохранении изображения: {e}")
        return None


def generate_comic_frame(prompt, frame_number):
    """Генерирует один кадр комикса и возвращает путь к сохраненному изображению"""
    print(f"\n🎨 Генерирую кадр {frame_number}...")
    print(f"📝 Промпт: {prompt}")

    generation_url = f"{API_BASE}/networks/{NETWORK_ID}"
    generation_data = {"prompt": prompt}

    try:
        gen_response = requests.post(generation_url, json=generation_data, headers=headers, timeout=30)

        if gen_response.status_code == 200:
            gen_result = gen_response.json()
            request_id = gen_result.get("request_id")

            if request_id:
                print(f"✅ Задача создана. request_id: {request_id}")

                # Ожидание и проверка результата
                status_url = f"{API_BASE}/request/get/{request_id}"

                for attempt in range(1, 31):
                    print(f"⏳ Проверяю статус... (попытка {attempt}/30)")
                    status_response = requests.get(status_url, headers=headers)

                    if status_response.status_code == 200:
                        status_result = status_response.json()
                        current_status = status_result.get("status")

                        if current_status == "success":
                            print(f"✅ Кадр {frame_number} сгенерирован!")

                            # ИСПРАВЛЕНИЕ: URL находится в поле 'result', а не 'output'
                            image_urls = status_result.get("result", [])

                            if image_urls and isinstance(image_urls, list) and len(image_urls) > 0:
                                image_url = image_urls[0]  # Берем первую ссылку из массива

                                if image_url and image_url.startswith('http'):
                                    print(f"📸 Найдено изображение: {image_url}")

                                    # Создаем имя файла
                                    timestamp = int(time.time())
                                    filename = f"comic_frame_{frame_number}_{timestamp}"
                                    saved_path = save_image_from_url(image_url, filename)

                                    if saved_path:
                                        print(f"🎉 Кадр {frame_number} успешно сохранен!")
                                        return saved_path
                                    else:
                                        print(f"❌ Не удалось сохранить кадр {frame_number}")
                                        return None
                                else:
                                    print(f"❌ Некорректный URL: {image_url}")
                                    return None
                            else:
                                print(f"❌ Массив result пуст или не содержит URL-ов: {image_urls}")
                                return None

                        elif current_status == "processing":
                            print(f"🔄 Кадр {frame_number} в обработке, жду 10 секунд...")
                            time.sleep(10)
                        elif current_status in ["failed", "error"]:
                            print(f"❌ Ошибка генерации кадра {frame_number}: {status_result}")
                            return None
                        else:
                            print(f"⚠️ Неизвестный статус для кадра {frame_number}: {current_status}")
                            time.sleep(10)
                    else:
                        print(f"❌ Ошибка проверки статуса: {status_response.status_code}")
                        return None

                print(f"⏰ Превышено время ожидания для кадра {frame_number}")
                return None
            else:
                print(f"❌ request_id не найден для кадра {frame_number}")
                return None
        else:
            print(f"❌ Ошибка HTTP при генерации: {gen_response.status_code}")
            print(f"Текст ответа: {gen_response.text}")
            return None

    except Exception as e:
        print(f"❌ Неожиданная ошибка при генерации кадра {frame_number}: {e}")
        return None


# Сценарий комикса - 4 кадра
comic_scenes = [
    "Комикс стиль: Супергерой в синем костюме стоит на крыше небоскреба, смотрит на город ночью, динамичная поза, яркие цвета, комикс панель",
    "Комикс стиль: Супергерой летит над городом, развевается плащ, вдали видны вспышки молний, стиль американского комикса",
    "Комикс стиль: Крупный план лица супергероя, решительное выражение, маска скрывает глаза, драматическое освещение",
    "Комикс стиль: Супергерой приземляется на улице, вокруг разлетаются обломки, злодей вдали, экшн сцена комикс"
]

print("🚀 Начинаю генерацию комикса из 4 кадров...")
print("=" * 50)

generated_images = []

for i, scene_prompt in enumerate(comic_scenes, 1):
    saved_path = generate_comic_frame(scene_prompt, i)
    if saved_path:
        generated_images.append(saved_path)
    else:
        print(f"❌ Не удалось сгенерировать кадр {i}")

    # Пауза между запросами
    if i < len(comic_scenes):
        print("⏸️  Пауза 5 секунд перед следующим кадром...")
        time.sleep(5)

print("\n" + "=" * 50)
print("🎉 Генерация комикса завершена!")

if generated_images:
    print(f"✅ Успешно сгенерировано кадров: {len(generated_images)}/{len(comic_scenes)}")
    print("📁 Сохраненные файлы:")
    for img_path in generated_images:
        print(f"   - {os.path.basename(img_path)}")

    print(f"\n💾 Все изображения сохранены в папке: {os.path.abspath(OUTPUT_FOLDER)}")
else:
    print("❌ Не удалось сгенерировать ни одного кадра")