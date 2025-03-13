import csv
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv
import os

load_dotenv()

# Настройки
BOT_TOKEN = os.getenv('BOT_TOKEN')
CSV_FILE = os.getenv('CSV_FILE')
USER_ID_COLUMN = os.getenv('USER_ID_COLUMN')
GAME_URL = os.getenv('GAME_URL')
MESSAGE_TEXT = (
    "Шопинг на полную катушку с Вики Шоу!\n\n"
    "С 14 по 29 марта в ТРЦ “Город Лефортово” — настоящая охота за призами! "
    "Делай покупки, сканируй чеки в чат-боте и лови крутые подарки в хватайке: "
    "мерч от Вики Шоу, сертификаты, брелки и стикерпаки!\n\n"
    "А 29 марта в 17:00 — грандиозная встреча на первом этаже! "
    "Концерт Вики Шоу, яркие эмоции и море веселья.\n\n"
    "Правила акции по команде /rules"
)

# Настройка логирования
logging.basicConfig(
    filename="distrib.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Создаем бота и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Счетчики успешных и неуспешных отправок
success_count = 0
failure_count = 0

def get_unique_user_ids(file_path, column_name):
    """Извлекает уникальные user_id из CSV файла с разделителем ;."""
    user_ids = set()
    try:
        # Проверяем, существует ли файл
        if not os.path.exists(file_path):
            logging.error(f"Файл {file_path} не найден.")
            print(f"Файл {file_path} не найден.")
            return user_ids

        with open(file_path, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file, delimiter=";")  # Указываем разделитель ;
            for row in reader:
                user_id = row.get(column_name)
                if user_id:
                    user_ids.add(user_id)
        logging.info(f"Загружено {len(user_ids)} уникальных user_id.")
        print(f"Загружено {len(user_ids)} уникальных user_id.")
    except Exception as e:
        logging.error(f"Ошибка при чтении файла {file_path}: {e}")
        print(f"Ошибка при чтении файла {file_path}: {e}")
    return user_ids

async def send_message(user_id):
    """Отправляет сообщение пользователю."""
    global success_count, failure_count  # Используем глобальные счетчики
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Вернуться в игру", url=GAME_URL)]
    ])
    try:
        await bot.send_message(chat_id=user_id, text=MESSAGE_TEXT, reply_markup=keyboard)
        logging.info(f"Сообщение отправлено: {user_id}")
        print(f"Сообщение отправлено: {user_id}")
        success_count += 1  # Увеличиваем счетчик успешных отправок
    except Exception as e:
        logging.error(f"Ошибка отправки для {user_id}: {e}")
        print(f"Ошибка отправки для {user_id}: {e}")
        failure_count += 1  # Увеличиваем счетчик неуспешных отправок

async def main():
    """Основная функция."""
    global success_count, failure_count  # Используем глобальные счетчики
    print("Скрипт запущен")
    logging.info("Скрипт запущен")
    logging.info(f"Используемый файл: {CSV_FILE}")

    # Проверяем, существует ли файл
    if not os.path.exists(CSV_FILE):
        logging.error(f"Файл {CSV_FILE} не найден.")
        print(f"Файл {CSV_FILE} не найден.")
        return

    user_ids = get_unique_user_ids(CSV_FILE, USER_ID_COLUMN)
    for user_id in user_ids:
        await send_message(user_id)
    
    # Выводим итоговую статистику
    print(f"\nИтоговая статистика:")
    print(f"Успешных отправок: {success_count}")
    print(f"Неуспешных отправок: {failure_count}")
    logging.info(f"Итоговая статистика: Успешных отправок - {success_count}, Неуспешных отправок - {failure_count}")

if __name__ == "__main__":
    asyncio.run(main())