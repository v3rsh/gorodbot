import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram import F
from aiogram.filters import Command
from aiogram import Router
from dotenv import load_dotenv
import asyncio

load_dotenv()

API_TOKEN = os.getenv('BOT_TOKEN')
GAME_URL = os.getenv('GAME_URL')
support_email = os.getenv('SUPPORT_EMAIL')

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Create router
router = Router()
dp.include_router(router)

keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Вход в мини-приложение", url=GAME_URL)]
])
# Command handler for /start
@router.message(Command(commands=['start']))


async def send_welcome(message: types.Message):
    # Create inline button for entering the miniapp
    await message.answer("Добро пожаловать в бот Города Лефортово!\n\nВы можете ознакомиться с правилами или войти в мини-приложение.", reply_markup=keyboard)

# Command handler for /rules
@router.message(Command(commands=['rules']))
async def rules(message: types.Message):
    text = (
        "Акция «Колесо Фортуны» проводится в целях повышения узнаваемости Торгового центра, популяризации его услуг, "
        "привлечения большего количества посетителей и/или покупателей и стимулирования к реализации всего ассортимента товаров магазинов, "
        "расположенных в Торговом центре.\n\n"
        "Акция не преследует цели получения прибыли либо иного дохода, не является лотереей, не содержит элементов риска, участие в Акции не связано с внесением платы Участниками "
        "и проводится в соответствии с положениями настоящих Правил и действующего законодательства РФ.\n\n"
        "Информирование Участников Акции проводится путем размещения настоящих Правил и информации об Акции для открытого доступа на странице Акции "
        "https://lefortovo-gorod.ru/ в течение периода с 18 ноября 2024г. по 18.00 часов 31 декабря 2024г. включительно.\n\n"
        "Территория проведения Акции (получения призов) – Российская Федерация. \n"
        "Офлайн площадка проведения Акции – г.Москва, ш. Энтузиастов, д.12, к.2, Торговый центр «ГОРОД» Лефортово. \n"
        "Онлайн площадки проведения Акции, а именно Активации «Колесо Фортуны»:\n"
        "• Приложение Акции в сети интернет: https://lefortovo-gorod.ru;\n"
        "• Чат-бот Акции в Telegram «Колесо Фортуны»: https://t.me/gorod_lefortovo_bot\n\n"
        "Участниками Акции, признаются лица, выполнившие все необходимые требования для участия в Акции, предусмотренные настоящими Правилами. "
        "Факт участия в Акции означает ознакомление и полное согласие Участников с настоящими Правилами.\n\n"
        "Полные правила акции доступны в мини-приложении."
    )
    
    await message.answer(text, reply_markup=keyboard, disable_web_page_preview=True)

# Command handler for /help
@router.message(Command(commands=['help']))
async def help_command(message: types.Message):
    text = (
        "Если у вас возникли вопросы по мероприятию «Колесо Фортуны», "
        "вы можете обратиться в нашу службу поддержки по электронной почте: "
        f"{support_email}"
    )
    await message.answer(text)

# Main function to start polling
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
