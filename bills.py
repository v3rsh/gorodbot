from flask import Flask, request, jsonify
import os
import logging
import requests
from PIL import Image
from io import BytesIO
import zxing
from pyzbar.pyzbar import decode
import tempfile
from dotenv import load_dotenv

load_dotenv()

# Настройка логирования
logging.basicConfig(filename='bills.log', level=logging.DEBUG, 
                    format='%(asctime)s %(levelname)s %(message)s')

app = Flask(__name__)

# Функция для корректировки ориентации изображения
def correct_image_orientation(image):
    try:
        exif = image._getexif()
        if exif is not None:
            orientation_key = 274  # Exif-тег 'Orientation'
            if orientation_key in exif:
                orientation = exif[orientation_key]
                if orientation == 3:
                    image = image.rotate(180, expand=True)
                elif orientation == 6:
                    image = image.rotate(270, expand=True)
                elif orientation == 8:
                    image = image.rotate(90, expand=True)
        return image
    except Exception as e:
        logging.error(f"Ошибка при корректировке ориентации изображения: {str(e)}")
        return image

# Функция для распознавания QR-кода с помощью pyzbar
def detect_qr_code_pyzbar(image_content):
    try:
        image = Image.open(image_content)
        image = correct_image_orientation(image)
        decoded_objects = decode(image)
        if decoded_objects:
            qr_data = decoded_objects[0].data.decode('utf-8')
            logging.info(f"QR-код распознан с помощью pyzbar: {qr_data}")
            return qr_data, 'pyzbar'
        else:
            logging.info("QR-код не найден с помощью pyzbar")
            return None, 'pyzbar'
    except Exception as e:
        logging.error(f"Ошибка при распознавании QR-кода с помощью pyzbar: {str(e)}")
        return None, 'pyzbar'

# Функция для распознавания QR-кода с помощью zxing
def detect_qr_code_zxing(image_content):
    try:
        image = Image.open(image_content)
        image = correct_image_orientation(image)
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            image.save(tmp_file, format='PNG')
            tmp_file_path = tmp_file.name
        try:
            reader = zxing.BarCodeReader()
            qr_result = reader.decode(tmp_file_path)
            if qr_result:
                qr_data = qr_result.parsed
                logging.info(f"QR-код распознан с помощью zxing: {qr_data}")
                return qr_data, 'zxing'
            else:
                logging.info("QR-код не найден с помощью zxing")
                return None, 'zxing'
        finally:
            os.unlink(tmp_file_path)
    except Exception as e:
        logging.error(f"Ошибка при распознавании QR-кода с помощью zxing: {str(e)}")
        return None, 'zxing'

@app.route('/bills', methods=['POST'])
def process_receipt():
    try:
        logging.debug(f"Получен запрос: headers={request.headers}, body={request.get_data(as_text=True)}, form_data={request.form}, files={request.files}")

        data = request.get_json()
        photo_url = data.get('photo')
        
        if not photo_url:
            logging.error("Отсутствует параметр photo в запросе")
            return jsonify({'status': 'Error', 'error': 'Отсутствует параметр photo'}), 400

        if not photo_url.startswith('http'):
            photo_url = 'https:' + photo_url
        
        logging.debug(f"Проверенный URL файла чека: {photo_url}")
        
        receipt_response = requests.get(photo_url)
        if receipt_response.status_code != 200:
            logging.error("Не удалось загрузить файл чека по указанному URL")
            return jsonify({'status': 'Error', 'error': 'Не удалось загрузить файл чека по указанному URL'}), 400

        image_content = BytesIO(receipt_response.content)
        
        # Попытка распознать QR-код с помощью pyzbar
        qr_data, method = detect_qr_code_pyzbar(image_content)
        if not qr_data:
            qr_data, method = detect_qr_code_zxing(image_content)
        
        if qr_data:
            logging.info(f"QR-код обнаружен с помощью {method}: {qr_data}")
            return jsonify({'status': 'Success', 'qr': True, 'data': qr_data})
        else:
            logging.info("QR-код не найден")
            return jsonify({'status': 'Error', 'qr': False, 'error': 'QR-код через обработку на сервере не найден'})

    except Exception as e:
        logging.error(f"Ошибка: {str(e)}")
        return jsonify({'status': 'Error', 'error': str(e)})

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5060)
