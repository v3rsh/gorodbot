from flask import Flask, request, jsonify
import os
import logging
import requests
from PIL import Image
from io import BytesIO
import pytesseract
import threading
from dotenv import load_dotenv
import json

load_dotenv()

BUBBLE_API_BASE_URL = os.getenv('BUBBLE_API_BASE_URL')
CHECK_API_URL = os.getenv('CHECK_API_URL')
CHECK_API_TOKEN = os.getenv('CHECK_API_TOKEN')
BUBBLE_WORKFLOW_API_URL = os.getenv('BUBBLE_WORKFLOW_API_URL')

# Настройка логирования
logging.basicConfig(filename='bills.log', level=logging.DEBUG, 
                    format='%(asctime)s %(levelname)s %(message)s')

app = Flask(__name__)

@app.route('/bills', methods=['POST'])
def process_receipt():
    try:
        # Логирование самого запроса
        logging.debug(f"Получен запрос: headers={request.headers}, body={request.get_data(as_text=True)}, form_data={request.form}, files={request.files}")

        # Проверка типа контента
        if request.content_type != 'application/json':
            logging.error("Неправильный Content-Type, требуется 'application/json'")
            return jsonify({'error': 'Неправильный Content-Type, требуется application/json'}), 400

        # Получение данных из POST-запроса
        data = request.get_json()
        user_id = data.get('user_id')
        bill_id = data.get('bill_id')
        photo_url = data.get('photo')

        if not user_id or not bill_id or not photo_url:
            logging.error("Не все обязательные параметры указаны в запросе")
            return jsonify({'error': 'Отсутствуют обязательные параметры'}), 400

        # Добавление префикса 'https:' если он отсутствует в URL
        if not photo_url.startswith('http'):
            photo_url = 'https:' + photo_url

        # Загрузка файла чека по URL и обрезка URL после разрешения файла
        trimmed_photo_url = photo_url.split('?')[0]
        logging.debug(f"Обрезанный URL файла чека: {trimmed_photo_url}")
        receipt_response = requests.get(trimmed_photo_url)
        if receipt_response.status_code != 200:
            logging.error("Не удалось загрузить файл чека по указанному URL")
            return jsonify({'error': 'Не удалось загрузить файл чека по указанному URL'}), 400

        # Получение бинарных данных изображения
        receipt_content = receipt_response.content

        # Сразу возвращаем положительный ответ об успешной загрузке файла
        logging.info("Файл чека успешно загружен, продолжаем обработку в фоне")
        bubble_response = jsonify({'status': 'Success'})

        # Фоновая обработка чека
        def background_processing():
            try:
                # Попытка отправить изображение на проверку через API
                logging.info("Отправка изображения на проверку через API")
                check_payload = {
                    'qrurl': trimmed_photo_url,
                    'token': CHECK_API_TOKEN
                }
                check_response = requests.post(CHECK_API_URL, data=check_payload)
                if check_response.status_code == 200:
                    response_data = check_response.json()
                    logging.info(f"Ответ от сервиса проверки чеков: {response_data}")
                    # Если чек успешно распознан, отправляем данные в Bubble
                    if response_data['code'] == 1:
                        json_data = response_data['data']['json']
                        bubble_payload = {
                            'bill_id': bill_id,
                            'user': user_id,
                            'fn': str(json_data.get('fiscalDriveNumber')),
                            'fd': str(json_data.get('fiscalDocumentNumber')),
                            'fp': str(json_data.get('fiscalSign')),
                            'check_time': json_data.get('dateTime'),
                            'type': json_data.get('operationType'),
                            'sum': json_data.get('totalSum') / 100,
                            'address': json_data.get('retailPlaceAddress'),  # Добавляем адрес
                            'api_json': json.dumps(response_data)  # Передаем полный ответ в параметре api_json как строку
                        }
                        workflow_url = f"{BUBBLE_WORKFLOW_API_URL}"
                        bubble_response = requests.post(workflow_url, json=bubble_payload)
                        if bubble_response.status_code == 200:
                            logging.info(f"Данные успешно отправлены в Bubble: {bubble_response.json()}")
                        else:
                            logging.error(f"Ошибка при отправке данных в Bubble: {bubble_response.status_code} - {bubble_response.text}")
                    return

                # Если QR-код не распознан, выполняем OCR для извлечения текста
                logging.info("QR-код не распознан, выполняется OCR обработка изображения")
                image = Image.open(BytesIO(receipt_content))
                receipt_text = pytesseract.image_to_string(image, lang='rus')
                logging.info(f"Извлеченный текст из чека: {receipt_text}")
                # Дополнительная обработка текста для формирования запроса вручную
                manual_payload = {
                    'fn': '...',  # Здесь следует добавить логику для извлечения нужных данных
                    'fd': '...',
                    'fp': '...',
                    'check_time': '...',
                    'type': '...',
                    'sum': '...'
                }
                check_manual_payload = {
                    **manual_payload,
                    'token': CHECK_API_TOKEN
                }
                manual_check_response = requests.post(CHECK_API_URL, data=check_manual_payload)
                if manual_check_response.status_code == 200:
                    logging.info(f"Ответ от сервиса проверки чеков (ручной запрос): {manual_check_response.json()}")
                else:
                    logging.error(f"Ошибка при ручной проверке чека: {manual_check_response.status_code} - {manual_check_response.text}")

            except Exception as e:
                logging.error(f"Ошибка в фоновом процессе: {str(e)}")

        threading.Thread(target=background_processing).start()

        return bubble_response

    except Exception as e:
        logging.error(f"Ошибка: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5060)
