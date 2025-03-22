import csv
import mysql.connector
from dotenv import load_dotenv
import os

# Загрузка переменных из .env
load_dotenv()

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

# Подключение к MySQL
conn = mysql.connector.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME
)
cursor = conn.cursor()

# Чтение CSV
with open('export.csv', newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        email = row['email_main'].strip()
        phone = row['phone'].strip()
        user_id = row['user_id'].strip()
        username = row['username'].strip()

        # Проверка, есть ли пользователь в базе
        cursor.execute("SELECT phone, email FROM users WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()

        if result:
            # Обновляем недостающие поля
            db_phone, db_email = result
            update_needed = False
            update_fields = []
            update_values = []

            if not db_phone and phone:
                update_fields.append("phone = %s")
                update_values.append(phone)
                update_needed = True

            if not db_email and email:
                update_fields.append("email = %s")
                update_values.append(email)
                update_needed = True

            if update_needed:
                update_values.append(user_id)
                query = f"UPDATE users SET {', '.join(update_fields)} WHERE user_id = %s"
                cursor.execute(query, tuple(update_values))
        else:
            # Добавляем нового пользователя
            cursor.execute("""
                INSERT INTO users (username, user_id, phone, email)
                VALUES (%s, %s, %s, %s)
            """, (username, user_id, phone, email))

# Сохраняем изменения
conn.commit()
cursor.close()
conn.close()

print("Готово: данные обновлены или добавлены.")
