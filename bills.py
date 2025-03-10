from flask import Flask, request, jsonify
import os
import logging
import requests
from PIL import Image
from io import BytesIO
import pytesseract
import re
from dotenv import load_dotenv
import zxing
import pillow_heif  # Поддержка HEIC через pillow-heif
from pyzbar.pyzbar import decode
import tempfile

load_dotenv()

# Настройка логирования
logging.basicConfig(filename='bills.log', level=logging.DEBUG, 
                    format='%(asctime)s %(levelname)s %(message)s')

app = Flask(__name__)

# Функция для проверки, нужно ли конвертировать изображение
def is_image_format_supported(image_content):
    try:
        image = Image.open(BytesIO(image_content))
        return image.format in ['JPEG', 'PNG', 'BMP', 'GIF', 'TIFF']
    except Exception as e:
        logging.error(f"Ошибка при определении формата изображения: {str(e)}")
        return False

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

def ocr_process_image(image_content):
    image = Image.open(image_content)
    image = correct_image_orientation(image)
    text = pytesseract.image_to_string(image, lang='rus')
    return text

def detect_qr_code_pyzbar(image_content):
    try:
        image = Image.open(image_content)
        image = correct_image_orientation(image)
        decoded_objects = decode(image)
        if decoded_objects:
            for obj in decoded_objects:
                qr_data = obj.data.decode('utf-8')
                logging.info(f"QR-код распознан с помощью pyzbar: {qr_data}")
                return qr_data, 'pyzbar'
        else:
            logging.info("QR-код не найден с помощью pyzbar")
            return None, 'pyzbar'
    except Exception as e:
        logging.error(f"Ошибка при распознавании QR-кода с помощью pyzbar: {str(e)}")
        return None, 'pyzbar'

def detect_qr_code_zxing(image_content):
    try:
        image = Image.open(image_content)
        image = correct_image_orientation(image)
        # Сохранение корректированного изображения во временный файл
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

# ... остальной код ...

# Функция для извлечения суммы из текста
def extract_sum(text):
    match = re.search(r'(сумма|итог)[\s:.,\-–—~=/\\]*([\d,]+\.\d{2})', text, re.IGNORECASE)
    return float(match.group(2).replace(',', '')) if match else None

# Функция для извлечения даты из текста
def extract_date(text):
    match = re.search(r'\d{2}[\s:.,\-–—~=/\\]*\d{2}[\s:.,\-–—~=/\\]*\d{4}[\s:.,\-–—~=/\\]*\d{2}[:\s:.,\-–—~=/\\]*\d{2}', text)
    return match.group() if match else None

# Функция для извлечения параметров чека
def extract_receipt_info(text):
    fn_match = re.search(r'ФН[\s:.,;\xab–—~=/\\]*\d{16}', text)
    fd_match = re.search(r'ФД[\s:.,;\xab–—~=/\\]*\d+', text)
    fp_match = re.search(r'ФП[\s:.,;\xab–—~=/\\]*\d+', text)
    
    fn = fn_match.group(0).split()[-1] if fn_match else None
    fd = fd_match.group(0).split()[-1] if fd_match else None
    fp = fp_match.group(0).split()[-1] if fp_match else None
    sum_value = extract_sum(text)
    date = extract_date(text)

    return fn, fd, fp, sum_value, date

# Функция для извлечения параметров из QR-кода
def parse_qr_data(qr_data):
    pattern = r"t=(?P<date>[\dT]+)&s=(?P<sum>[\d.]+)&fn=(?P<fn>\d+)&i=(?P<fd>\d+)&fp=(?P<fp>\d+)&n=(?P<i>\d+)"
    match = re.search(pattern, qr_data)
    
    if match:
        return {
            'date': match.group('date'),
            'sum': float(match.group('sum')),
            'fn': match.group('fn'),
            'fd': match.group('fd'),
            'fp': match.group('fp'),
            'i': int(match.group('i'))
        }
    else:
        logging.info("Не удалось извлечь необходимые параметры из QR-кода")
        return None

# Функция для извлечения всех числовых комбинаций из текста
def extract_all_numbers(text):
    return [f'"{number}"' for number in re.findall(r'\d{3,}', text)]

# Функция для определения типа операции
def extract_operation_type(text):
    match = re.search(r'(приход|расход|возврат прихода)', text, re.IGNORECASE)
    if match:
        operation = match.group(0).lower()
        if operation == 'приход':
            return 1
        elif operation == 'расход':
            return 3
        elif operation == 'возврат прихода':
            return 2
    return None

@app.route('/bills', methods=['POST'])
def process_receipt():
    try:
        logging.debug(f"Получен запрос: headers={request.headers}, body={request.get_data(as_text=True)}, form_data={request.form}, files={request.files}")

        # Получение данных из POST-запроса
        data = request.get_json()
        user_id = data.get('user_id')
        bill_id = data.get('bill_id')
        photo_url = data.get('photo')

        # Проверка и добавление префикса 'https:' если он отсутствует в URL
        if not photo_url.startswith('http'):
            photo_url = 'https:' + photo_url
        logging.debug(f"Проверенный и исправленный URL файла чека: {photo_url}")

        # Загрузка файла чека по URL
        trimmed_photo_url = photo_url.split('?')[0]
        logging.debug(f"Обрезанный URL файла чека: {trimmed_photo_url}")
        receipt_response = requests.get(trimmed_photo_url)
        if receipt_response.status_code != 200:
            logging.error("Не удалось загрузить файл чека по указанному URL")
            return jsonify({'status': 'Error', 'error': 'Не удалось загрузить файл чека по указанному URL'}), 400

        image_content = receipt_response.content

        # Проверяем, нужно ли конвертировать изображение
        if not is_image_format_supported(image_content):
            # Конвертация изображения в PNG перед обработкой
            image = Image.open(BytesIO(image_content))
            png_image = BytesIO()
            image.convert("RGB").save(png_image, format="PNG")
            png_image.seek(0)
            image_content = png_image.getvalue()
            logging.info("Изображение было сконвертировано в PNG для обработки")
        else:
            logging.info("Изображение в поддерживаемом формате, конвертация не требуется")
            image_content = BytesIO(image_content)

        # OCR обработка изображения
        receipt_text = ocr_process_image(image_content)
        logging.info(f"Извлеченный текст из чека: {receipt_text}")

        # Извлекаем все числовые комбинации из текста
        raw_numbers = extract_all_numbers(receipt_text)
        logging.info(f"Все числовые комбинации, найденные в тексте: {raw_numbers}")

        # Попытка распознать QR-код с помощью pyzbar
        qr_data, method = detect_qr_code_pyzbar(image_content)
        if not qr_data:
            # Если не удалось, пробуем с помощью zxing
            qr_data, method = detect_qr_code_zxing(image_content)
        
        if qr_data:
            logging.info(f"QR-код обнаружен с помощью {method}: {qr_data}")
            parsed_data = parse_qr_data(qr_data)
            if parsed_data:
                logging.info(f"QR-код содержит все необходимые параметры: {parsed_data}")
                return jsonify({'status': 'Success', 'qr': True, 'params': parsed_data, 'raw_numbers': raw_numbers, 'error': None})
        else:
            logging.info("QR-код не обнаружен ни одним из методов")

        # Извлекаем данные из текста и проверяем каждый параметр
        fn, fd, fp, sum_value, date = extract_receipt_info(receipt_text)
        operation_type = extract_operation_type(receipt_text)
        
        missing_params = []
        if not fn:
            missing_params.append("ФН")
        if not fd:
            missing_params.append("ФД")
        if not fp:
            missing_params.append("ФП")
        if not sum_value:
            missing_params.append("сумма")
        if not date:
            missing_params.append("дата")
        if not operation_type:
            missing_params.append("тип операции")

        if missing_params:
            error_msg = f"Не найдены параметры: {', '.join(missing_params)}"
            logging.error(error_msg)
            return jsonify({'status': 'Error', 'qr': False, 'error': error_msg})

        # Логируем все параметры при успешном извлечении
        logging.info(f"Все параметры успешно найдены: ФН={fn}, ФД={fd}, ФП={fp}, сумма={sum_value}, дата={date}, тип операции={operation_type}. Возвращаем успешный ответ")
        return jsonify({
            'status': 'Success', 
            'qr': False, 
            'params': {
                'fn': fn,
                'fd': fd,
                'fp': fp,
                'sum': sum_value,
                'date': date,
                'operation_type': operation_type
            }, 
            'raw_numbers': raw_numbers,
            'error': None
        })

    except Exception as e:
        logging.error(f"Ошибка: {str(e)}")
        return jsonify({'status': 'Error', 'error': str(e)})

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5060)
