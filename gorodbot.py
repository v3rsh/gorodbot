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
    [InlineKeyboardButton(text="Вход в мини-приложение", url=GAME_URL)],
    [InlineKeyboardButton(text="Вход с параметром", url="https://gorod-lefortovo.bubbleapps.io?param=10")]
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
        "Акция «Шопинг на полную катушку» проводится в целях повышения узнаваемости Торгового центра, популяризации его услуг, "
        "привлечения большего количества посетителей и/или покупателей и стимулирования к реализации всего ассортимента товаров магазинов, "
        "расположенных в Торговом центре.\n\n"
        "Акция не преследует цели получения прибыли либо иного дохода, не является лотереей, не содержит элементов риска, участие в Акции не связано с внесением платы Участниками "
        "и проводится в соответствии с положениями настоящих Правил и действующего законодательства РФ.\n\n"
        "Информирование Участников Акции проводится путем размещения настоящих Правил и информации об Акции для открытого доступа на странице Акции "
        "vikishow.lefortovo-gorod.ru в течение срока, указанного в п.4.2 настоящих Правил.\n\n"
        "Территория проведения Акции (получения призов) – Российская Федерация. \n"
        "Офлайн площадка проведения Акции – г.Москва, ш. Энтузиастов, д.12, к.2, Торговый центр «ГОРОД» Лефортово. \n"
        "Онлайн площадки проведения Акции «Шопинг на полную катушку»:\n"
        "● Приложение Акции в сети интернет: vikishow.lefortovo-gorod.ru;\n"
        "● Чат-бот Акции в Telegram «ГОРОД Лефортово»: https://t.me/gorod_lefortovo_bot.\n\n"
        "Единоразовая покупка товара и/или услуг в одном из магазинов или ресторанов Торгового центра, за исключением банков, банкоматов, вендинговых автоматов и терминалов оплаты сотовой связи и торговых точках Арендаторов Торгового Центра, указанных в п.2.9 настоящих Правил, на сумму не менее 3 000,00 (Три тысячи) рублей 00 копеек, (чеки за покупки/услуги, совершенные до даты начала Акции не участвуют в Акции, чеки не суммируются) и регистрация чека посредством функционала Страницы Акции или Чат-бота в Telegram «Шопинг на полную катушку» является обязательным условием участия пользователя Страницы в Акции.\n\n"
        "В Акции не участвуют Чеки, полученные за покупки или операции с денежными средствами, в следующих организациях и торговых точках, являющихся Арендаторами Торгового Центра:\n"
        "● Банки, в том числе ПАО «Сбербанк России» и АО КБ «ЮНИСТРИМ»;\n"
        "● Банкоматы;\n"
        "● Вендинговые автоматы;\n"
        "● Терминалы оплаты сотовой связи.\n\n"
        "Полные правила акции в мини-приложении."
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
