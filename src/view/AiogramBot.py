import asyncio, os, time
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

dp = Dispatcher()

async def sim_msg():
    await asyncio.sleep(4)
    return "Result from bot - 4 sec"

def get_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="Ask a question", callback_data=print("test"))
    builder.button(text="Get training data")
    builder.adjust(2)


    return builder.as_markup(resize_keyboard=True, input_field_placeholder="Select action", is_persistent=True)



@dp.message(CommandStart())
async def cmd_start(msg: types.Message) -> None:
    await msg.answer(text="> Ask the AI questions useing the /ask command then rate the response for training\n"
                          "> Use /getdata command to see which data I am trained on", reply_markup=get_keyboard())
    # await msg.answer(text=await sim_msg())

async def main() -> None:
    bot = Bot(TELEGRAM_BOT_TOKEN)

    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())