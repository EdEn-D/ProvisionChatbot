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

router = Router()

# TODO: Restructure bot code

# Flow:
# 1. Start -> get buttons, ask Q, get data
# 2.1 Get data -> Print trained data
# 2.2 Ask Q -> Waiting for question
# 3 Waiting for response


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

@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(text="> Ask the AI questions using the buttons below\n"
                          "> Get the data to see which data I am trained on",
                     reply_markup=send_buttons(["Ask a question", "Get Training Data"])
                     )

@router.message(Command("Get Training Data"))
async def get_data(message: Message, state: FSMContext):
    await message.answer(text="Printing data...")
    print("Printing data...")

@router.message(F.text == "Ask a question")
async def ask_question(message: Message, state:FSMContext):
    await message.answer("Please ask your question: ")
    await state.set_state(Form.return_response)

@router.message(Form.return_response)
async def ask_rating(message: Message, state:FSMContext):
    await message.answer("Asking question, please wait...")
    print(f"asking question: {message.text}")
    response = await invoke_prompt(message.text)
    await message.answer(text=response)
    await message.answer(text="Is this correct?",
                         reply_markup=send_buttons(["Correct", "Incorrect"])
                         )
    await state.set_state(Form.rating)

@router.message(Form.rating)
async def ask_comments(message: Message, state: FSMContext):
    # save messsage.text
    await state.set_state(Form.comments)
    await message.answer("Thanks, any comments?")


@router.message(Form.comments)
async def final_message(message: Message, state: FSMContext):
    # save messsage.text
    await state.clear()
    await message.answer("Thank you for your feedback! Feel free to ask me some more questions!")
    await cmd_start(message)


async def ask_ai_and_log(message: Message, state: FSMContext):
    response = invoke_prompt(message.text)
    await response
    print(response)




async def main() -> None:
    bot = Bot(TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())