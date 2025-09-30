import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4


def convert_to_pdf(input_path):
    """
    Базовая конвертация файла в PDF
    """
    # Создаем временный файл для PDF
    output_path = os.path.splitext(input_path)[0] + '.pdf'

    # Создаем PDF
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    # Добавляем базовый текст
    c.setFont("Helvetica", 16)
    c.drawString(100, height - 100, f"Converted file: {os.path.basename(input_path)}")

    c.setFont("Helvetica", 12)
    c.drawString(100, height - 130, "This is a basic PDF conversion.")

    # Для текстовых файлов читаем содержимое
    if input_path.endswith('.txt'):
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Добавляем содержимое в PDF
            text = c.beginText(100, height - 160)
            text.setFont("Helvetica", 10)

            # Добавляем текст по строкам
            lines = content.split('\n')
            for line in lines[:30]:  # Ограничиваем количество строк
                if text.getY() < 100:  # Проверяем, не достигли ли низа страницы
                    c.drawText(text)
                    c.showPage()
                    text = c.beginText(100, height - 100)
                    text.setFont("Helvetica", 10)

                text.textLine(line[:80])  # Ограничиваем длину строки

            c.drawText(text)

        except Exception as e:
            c.drawString(100, height - 160, f"Error reading file: {str(e)}")

    c.save()
    return output_path