import requests
import os
import json
import logging
import base64
import csv
from dotenv import load_dotenv
from flask import Flask, request, jsonify

# Настройка логирования
logging.basicConfig(
    filename='/mike/bots/gorodbot/app.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)

# Загрузка переменных окружения
load_dotenv()

BUBBLE_API_URL = os.getenv('BUBBLE_API_URL')
BUBBLE_API_KEY = os.getenv('BUBBLE_API_KEY')

app = Flask(__name__)

def create_spins_bulk(amount, prize_id, sector, participate, prize_type, prize_name=None, photo_url=None):
    bulk_size = 1000  # Максимальное количество записей за один запрос
    used = "no"
    headers = {
        'Content-Type': 'text/plain',
        'Authorization': f'Bearer {BUBBLE_API_KEY}'
    }

    logging.info(f"Начало создания спинов: amount={amount}, prize_id={prize_id}, sector={sector}, participate={participate}, prize_name={prize_name}, prize_type={prize_type}")

    for i in range(0, amount, bulk_size):
        current_amount = min(bulk_size, amount - i)
        
        spins = [{
            'prize_id': prize_id,
            'participate': participate,
            'sector': sector,
            'used': used,
            'prize_type': prize_type,
            'prize_name': prize_name,
            'photo': photo_url
        } for _ in range(current_amount)]

        data = "\n".join([json.dumps(spin) for spin in spins])

        logging.info(f'Bubble API URL: {BUBBLE_API_URL}spin/bulk')
        logging.info(f'Заголовки запроса: {headers}')
        logging.info(f'Отправка данных в Bubble API:\n{data}')

        response = requests.post(f"{BUBBLE_API_URL}spin/bulk", headers=headers, data=data)
        if response.status_code == 200:
            logging.info(f"Успешно создано {current_amount} спинов")
        else:
            logging.error(f"Ошибка при создании спинов: {response.status_code} - {response.text}")

def create_spins_one_by_one(folder, prize_id, sector, participate, prize_name, prize_type):
    used = "no"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {BUBBLE_API_KEY}'
    }

    logging.info(f"Начало создания спинов поштучно: folder={folder}, prize_id={prize_id}, sector={sector}, participate={participate}, prize_name={prize_name}, prize_type={prize_type}")

    files = os.listdir(folder)
    total_created = 0

    for file_name in files:
        file_path = os.path.join(folder, file_name)

        # Закодируем изображение в Base64
        try:
            with open(file_path, 'rb') as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

            spin_data = {
                'prize_id': prize_id,
                'participate': participate,
                'sector': sector,
                'used': used,
                'prize_type': prize_type,
                'prize_name': prize_name,  # Добавили поле prize_name
                'photo': {
                    'filename': file_name,
                    'contents': encoded_image,
                    'private': False,
                    'attach_to': None
                }
            }

            # Отправляем запрос на создание одного спина
            logging.info(f'Отправка данных в Bubble API для файла {file_name}')
            response = requests.post(f"{BUBBLE_API_URL}spin", headers=headers, json=spin_data)
            if response.status_code == 200:
                logging.info(f"Успешно создан спин для файла {file_name}")
                total_created += 1
            else:
                logging.error(f"Ошибка при создании спина для файла {file_name}: {response.status_code} - {response.text}")

        except Exception as e:
            logging.error(f"Ошибка при обработке файла {file_name}: {str(e)}")

    # Делаем Patch запрос с обновлением количества созданных записей
    patch_url = f"{BUBBLE_API_URL}prize/{prize_id}"
    patch_data = {
        "amount": total_created
    }

    response = requests.patch(patch_url, headers=headers, json=patch_data)
    if response.status_code == 200:
        logging.info(f"Успешно обновлено количество созданных записей для приза {prize_id}")
    else:
        logging.error(f"Ошибка при обновлении количества записей для приза {prize_id}: {response.status_code} - {response.text}")

def create_spins_one_by_one_with_csv(folder, prize_id, sector, participate, prize_type, prize_name=None, photo_url=None):
    # Split folder to get the directory, file, and column name
    try:
        folder_parts = folder.split('/')
        directory = '/'.join(folder_parts[:-1])
        file_info = folder_parts[-1]
        csv_filename, column_name = file_info.split('?')
        csv_filename = os.path.join(directory, csv_filename)
    except ValueError:
        logging.error(f"Invalid folder parameter format: {folder}")
        return

    # Check if CSV file exists
    if not os.path.isfile(csv_filename):
        logging.error(f"CSV file does not exist: {csv_filename}")
        return

    used = "no"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {BUBBLE_API_KEY}'
    }

    logging.info(f"Processing spins with CSV: {csv_filename}, prize_id={prize_id}, sector={sector}, participate={participate}, prize_name={prize_name}, prize_type={prize_type}")

    # Read CSV and get the column with promocodes
    total_created = 0
    try:
        with open(csv_filename, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            if column_name not in reader.fieldnames:
                logging.error(f"Column '{column_name}' not found in CSV file {csv_filename}")
                return

            for row in reader:
                promocode = row.get(column_name)
                if not promocode:
                    logging.warning(f"Missing promocode in row: {row}")
                    continue

                spin_data = {
                    'prize_id': prize_id,
                    'participate': participate,
                    'sector': sector,
                    'used': used,
                    'prize_type': prize_type,
                    'prize_name': prize_name,
                    'photo': photo_url,  # Use photo URL directly from bubble request
                    'promocode': promocode
                }

                # Send the request to create one spin entry
                logging.info(f'Creating spin with promocode {promocode}')
                response = requests.post(f"{BUBBLE_API_URL}spin", headers=headers, json=spin_data)
                if response.status_code == 200:
                    logging.info(f"Successfully created spin for promocode {promocode}")
                    total_created += 1
                else:
                    logging.error(f"Error creating spin for promocode {promocode}: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"Error processing CSV file: {str(e)}")

    # Update the amount created in Bubble
    patch_url = f"{BUBBLE_API_URL}prize/{prize_id}"
    patch_data = {
        "amount": total_created
    }

    response = requests.patch(patch_url, headers=headers, json=patch_data)
    if response.status_code == 200:
        logging.info(f"Successfully updated the amount of created spins for prize {prize_id}")
    else:
        logging.error(f"Error updating the amount for prize {prize_id}: {response.status_code} - {response.text}")

@app.route('/getspins', methods=['GET', 'POST'])
def receive_signal():
    try:
        # Логирование сырых данных запроса
        raw_data = request.get_data(as_text=True)
        logging.info(f'Raw request data: {raw_data}')

        # Попытка получить JSON из запроса
        data = request.get_json()
        if data is None:
            logging.error('Не удалось получить JSON из запроса')
            return jsonify({'error': 'Invalid JSON'}), 400
        logging.info(f'Получены данные от Bubble: {data}')

        # Извлекаем параметры из запроса
        amount = data.get('amount')
        prize_id = data.get('prize_id')
        sector = data.get('sector')
        participate = data.get('participate')
        folder = data.get('folder')
        prize_name = data.get('prize_name')
        prize_type = data.get('prize_type')
        photo_url = data.get('photo')  # В сценарии 1 это URL фото
        if photo_url == "null" or not photo_url:  # Если "null" или пустое значение
            photo_url = None
        adding_type = data.get('adding_type')
        scenario = data.get('scenario')

        # Преобразуем типы данных
        try:
            if amount is not None:
                amount = int(amount)
            if sector is not None:
                sector = int(sector)
            if isinstance(participate, str):
                # Преобразуем 'Yes'/'No' в True/False
                participate = participate.lower() == 'yes'
            if isinstance(scenario, int):
                scenario = str(scenario)
        except ValueError as e:
            logging.error(f'Ошибка преобразования типов данных: {e}')
            return jsonify({'error': 'Invalid data types in request'}), 400

        # Проверяем значение scenario и вызываем соответствующую функцию
        if scenario == "1" and adding_type == "all_together":
            # Обработка сценария 1
            if not all([amount is not None, prize_id, sector is not None, participate is not None]):
                logging.error('Отсутствуют необходимые поля для сценария 1')
                return jsonify({'error': 'Missing required fields'}), 400

            create_spins_bulk(amount, prize_id, sector, participate, prize_type, prize_name, photo_url)

        elif scenario == "3" and adding_type == "one_by_one" and not photo_url:
            # Обработка сценария 3, если photo_url пустой
            if None in (folder, prize_id, sector, participate):
                logging.error('Отсутствуют необходимые поля для сценария 3')
                return jsonify({'error': 'Missing required fields'}), 400
            create_spins_one_by_one(folder, prize_id, sector, participate, prize_name, prize_type)
            
        elif scenario == "1" and adding_type == "one_by_one" and photo_url:
            # Обработка сценария 4, если photo_url не пустой
            create_spins_one_by_one_with_csv(folder, prize_id, sector, participate, prize_type, prize_name, photo_url)

        else:
            logging.error('Неверный сценарий или adding_type')
            return jsonify({'error': 'Invalid scenario or adding_type'}), 400

        logging.info('Сигнал успешно обработан')
        return jsonify({'status': 'Signal received'}), 200

    except Exception as e:
        logging.exception(f'Исключение в receive_signal: {e}')
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5050)
