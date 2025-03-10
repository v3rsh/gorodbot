import csv
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv

load_dotenv()

# Настройки
BOT_TOKEN = os.getenv('TELEGRAM_API_TOKEN')
CSV_FILE = os.getenv('CSV_FILE')
USER_ID_COLUMN = os.getenv('USER_ID_COLUMN')
GAME_URL = os.getenv('GAME_URL')
MESSAGE_TEXT = "Привет! У тебя есть неиспользованные попытки в Колесе фортуны ТРЦ Город Лефортово! Вернись в игру и используй шанс."

# Настройка логирования
logging.basicConfig(
    filename="distrib.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Создаем бота и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def get_unique_user_ids(file_path, column_name):
    """Извлекает уникальные user_id из CSV файла с разделителем ;."""
    user_ids = set()
    try:
        with open(file_path, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file, delimiter=";")  # Указываем разделитель ;
            for row in reader:
                user_id = row.get(column_name)
                if user_id:
                    user_ids.add(user_id)
        logging.info(f"Загружено {len(user_ids)} уникальных user_id.")
        print(f"Загружено {len(user_ids)} уникальных user_id.")
    except FileNotFoundError:
        logging.error(f"Файл {file_path} не найден.")
        print(f"Файл {file_path} не найден.")
    except Exception as e:
        logging.error(f"Ошибка при чтении файла {file_path}: {e}")
        print(f"Ошибка при чтении файла {file_path}: {e}")
    return user_ids

async def send_message(user_id):
    """Отправляет сообщение пользователю."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Вернуться в игру", url=GAME_URL)]
    ])
    try:
        await bot.send_message(chat_id=user_id, text=MESSAGE_TEXT, reply_markup=keyboard)
        logging.info(f"Сообщение отправлено: {user_id}")
        print(f"Сообщение отправлено: {user_id}")
    except Exception as e:
        logging.error(f"Ошибка отправки для {user_id}: {e}")
        print(f"Ошибка отправки для {user_id}: {e}")

async def main():
    """Основная функция."""
    print("Скрипт запущен")
    logging.info("Скрипт запущен")
    user_ids = get_unique_user_ids(CSV_FILE, USER_ID_COLUMN)
    for user_id in user_ids:
        await send_message(user_id)

if __name__ == "__main__":
    asyncio.run(main())
