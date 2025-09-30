from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename
import os
import tempfile
from converter import convert_to_pdf

app = Flask(__name__)

# Используем временную папку системы
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file uploaded', 400

    file = request.files['file']
    if file.filename == '':
        return 'No file selected', 400

    if file:
        try:
            # Создаем временные файлы
            with tempfile.NamedTemporaryFile(delete=False, suffix='_' + secure_filename(file.filename)) as input_temp:
                input_path = input_temp.name
                file.save(input_path)

            # Конвертируем в PDF
            pdf_path = convert_to_pdf(input_path)

            # Отправляем PDF пользователю
            response = send_file(
                pdf_path,
                as_attachment=True,
                download_name=f'{os.path.splitext(secure_filename(file.filename))[0]}.pdf'
            )

            # Удаляем временные файлы после отправки
            @response.call_on_close
            def cleanup():
                try:
                    if os.path.exists(input_path):
                        os.remove(input_path)
                    if os.path.exists(pdf_path):
                        os.remove(pdf_path)
                except:
                    pass  # Игнорируем ошибки при удалении

            return response

        except Exception as e:
            # Очистка в случае ошибки
            try:
                if 'input_path' in locals() and os.path.exists(input_path):
                    os.remove(input_path)
                if 'pdf_path' in locals() and os.path.exists(pdf_path):
                    os.remove(pdf_path)
            except:
                pass
            return f'Error converting file: {str(e)}', 500


if __name__ == '__main__':
    app.run(debug=True)
