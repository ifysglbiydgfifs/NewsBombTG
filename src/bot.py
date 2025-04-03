import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import config

logging.basicConfig(level=logging.INFO)

dp = Dispatcher()

keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="/start"),
            KeyboardButton(text="/help"),
        ],
        [
            KeyboardButton(text="/info"),
        ]
    ],
    resize_keyboard=True
)

@dp.message(Command("start"))
async def command_start_handler(message: Message) -> None:
    await message.answer(message.text, keyboard)
    
async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=config.bot_token.get_secret_value())

    # And the run events dispatching
    await dp.start_polling(bot)
    
if __name__ == "__main__":
    asyncio.run(main())