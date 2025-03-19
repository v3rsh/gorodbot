import csv
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path="./.env", override=True)

# Настройки
BOT_TOKEN = os.getenv('BOT_TOKEN')
CSV_FILE = os.getenv('CSV_FILE')           # Исходный CSV (users.csv)
USER_ID_COLUMN = os.getenv('USER_ID_COLUMN')  # Например, "user_id"
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

print("BOT_TOKEN =", BOT_TOKEN)
print("CSV_FILE =", CSV_FILE)

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

def read_users(file_path, user_id_col="user_id", username_col="username"):
    """
    Считывает исходный CSV с разделителем ; и возвращает список словарей вида:
    [{ "user_id": "...", "username": "..." }, ...].
    Если username_col не найден, пишем пустую строку.
    """
    users_data = []
    try:
        if not os.path.exists(file_path):
            logging.error(f"Файл {file_path} не найден.")
            print(f"Файл {file_path} не найден.")
            return users_data

        with open(file_path, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file, delimiter=";")
            for row in reader:
                if not row.get(user_id_col):
                    # Нет user_id — пропускаем
                    continue
                users_data.append({
                    "user_id": row.get(user_id_col, "").strip(),
                    "username": row.get(username_col, "").strip()
                })

        logging.info(f"Загружено {len(users_data)} строк (user_id, username).")
        print(f"Загружено {len(users_data)} строк (user_id, username).")
    except Exception as e:
        logging.error(f"Ошибка при чтении файла {file_path}: {e}")
        print(f"Ошибка при чтении файла {file_path}: {e}")

    return users_data

async def send_message(user_id):
    """
    Отправляет сообщение пользователю, возвращает строку статуса.
    Возвращаемое значение мы будем записывать в колонку status.
    """
    global success_count, failure_count
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Вернуться в игру", url=GAME_URL)]
    ])
    try:
        await bot.send_message(chat_id=user_id, text=MESSAGE_TEXT, reply_markup=keyboard)
        logging.info(f"Сообщение отправлено: {user_id}")
        print(f"Сообщение отправлено: {user_id}")
        success_count += 1
        return "sent"  # или можно вернуть более развернутый текст
    except Exception as e:
        logging.error(f"Ошибка отправки для {user_id}: {e}")
        print(f"Ошибка отправки для {user_id}: {e}")
        failure_count += 1
        return f"error: {e}"

async def main():
    global success_count, failure_count
    print("Скрипт запущен")
    logging.info("Скрипт запущен")
    logging.info(f"Используемый файл: {CSV_FILE}")

    # Проверяем, существует ли файл
    if not os.path.exists(CSV_FILE):
        logging.error(f"Файл {CSV_FILE} не найден.")
        print(f"Файл {CSV_FILE} не найден.")
        return

    # Считываем пользователей (user_id, username) из исходного файла
    users_data = read_users(
        file_path=CSV_FILE,
        user_id_col=USER_ID_COLUMN,
        username_col="username"   # <-- Если у вас иная колонка с username, поменяйте здесь
    )

    # Сюда будем собирать результаты рассылки
    results = []

    # Рассылаем сообщения и фиксируем результат
    for item in users_data:
        user_id = item["user_id"]
        username = item["username"]

        if not user_id:
            # Пропускаем "пустые" строки
            continue

        # Статус отправки
        status = await send_message(user_id)

        # Добавляем в список результатов
        results.append({
            "user_id": user_id,
            "username": username,
            "status": status
        })

    # Пишем отчет в новый CSV (не трогаем исходный файл)
    output_file = "distribution_report.csv"
    try:
        with open(output_file, mode="w", encoding="utf-8", newline="") as f:
            fieldnames = ["user_id", "username", "status"]
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
            writer.writeheader()
            writer.writerows(results)
        print(f"\nОтчет сформирован в файле: {output_file}")
    except Exception as e:
        logging.error(f"Ошибка при записи файла {output_file}: {e}")
        print(f"Ошибка при записи файла {output_file}: {e}")

    # Выводим итоговую статистику
    print(f"\nИтоговая статистика:")
    print(f"Успешных отправок: {success_count}")
    print(f"Неуспешных отправок: {failure_count}")
    logging.info(f"Итоговая статистика: Успешных отправок - {success_count}, Неуспешных отправок - {failure_count}")
    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
