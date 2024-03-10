import asyncio, os, time
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, ReplyKeyboardMarkup
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext

from states import Form
from TechSupportBot import invoke_prompt

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

dp = Dispatcher()
# router = Router

async def sim_msg():
    await asyncio.sleep(4)
    return "Result from bot - 4 sec"

# Helper function to send buttons
def send_buttons(buttons: list[str]) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    [builder.button(text=txt) for txt in buttons]
    return builder.as_markup(resize_keyboard=True, input_field_placeholder="Select action", one_time_keyboard=True, is_persistent=True)

def get_keyboard():

    builder = ReplyKeyboardBuilder()
    builder.button(text="Ask a question", callback_data=print("test"))
    builder.button(text="Get training data")
    builder.adjust(2)

@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(text="> Ask the AI questions useing the /ask command then rate the response for training\n"
                          "> Use /getdata command to see which data I am trained on",
                     reply_markup=send_buttons(["Ask a question", "Get Training Data"])
                     )

@dp.message(F.text == "Ask a question")
async def waiting_for_question(message: Message, state:FSMContext):
    await message.answer("Please ask your question: ")
    await state.set_state(Form.awaiting_query)

@dp.message(Form.awaiting_query)
async def ask_question(message: Message, state:FSMContext):
    await message.answer("Asking question, please wait...")
    print(f"asking question: {message.text}")
    response = await invoke_prompt(message.text)
    await state.set_state(Form.returning_response)
    await message.answer(text=response)
    await message.answer(text="Is this correct?")


@dp.message(Command("Get Training Data"))
async def get_data(message: Message, state:FSMContext):
    await message.answer(text="Printing data...")
    print("Printing data...")


async def ask_ai_and_log(message: Message, state: FSMContext):
    response = invoke_prompt(message.text)
    await response
    print(response)




async def main() -> None:
    bot = Bot(TELEGRAM_BOT_TOKEN)

    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())