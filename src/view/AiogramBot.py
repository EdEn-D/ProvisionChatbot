import asyncio, os, time
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, ReplyKeyboardMarkup
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext

from states import Form
from TechSupportBot import invoke_prompt, get_embedded_data, prepare_documents
from src.utils.df_logger import Logger

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
# logger = Logger()
loggers = {}  # Dictionary to hold Logger instances by chat_id
router = Router()

# TODO: Restructure bot code

# Flow:
# 1. Start -> get buttons, ask Q, get data
# 2.1 Get data -> Print trained data
# 2.2 Ask Q -> Waiting for question
# 3 Waiting for response

async def parse_docs(docs) -> str:
    ret = ""
    for i, doc in enumerate(docs):
        ret += f"Doc #{i}: {doc.metadata}\n"

    return ret


# Helper function to send buttons
def send_buttons(buttons: list[str]) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    [builder.button(text=txt) for txt in buttons]
    return builder.as_markup(resize_keyboard=True, input_field_placeholder="Select action", one_time_keyboard=True, is_persistent=True)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(text="> Ask the AI questions using the buttons below\n"
                          "> Get the data to see which data I am trained on",
                     reply_markup=send_buttons(["Ask a question", "Get Training Data"])
                     )

@router.message(F.text == "Get Training Data")
async def get_data(message: Message, state: FSMContext):
    await message.answer(text=get_embedded_data())

@router.message(F.text == "Ask a question")
async def ask_question(message: Message, state:FSMContext):
    loggers[message.from_user.id] = Logger()
    await message.answer(f"Hello {message.from_user.first_name}!\n"
                         f"Please ask your question: ")
    await loggers[message.from_user.id].set_user(message.from_user.first_name)
    await state.set_state(Form.return_response)

@router.message(Form.return_response)
async def ask_rating(message: Message, state:FSMContext):
    await message.answer("Asking question, please wait...")
    print(f"asking question: {message.text}")
    await loggers[message.from_user.id].set_query(message.text)
    response_docs = await invoke_prompt(message.text)
    response = response_docs[0]
    docs = await parse_docs(response_docs[1])
    await message.answer(text=response)
    await message.answer(text=docs)
    await loggers[message.from_user.id].set_response(response)
    await message.answer(text="Is this correct?",
                         reply_markup=send_buttons(["Correct", "Incorrect"])
                         )
    await state.set_state(Form.rating)

@router.message(Form.rating)
async def ask_comments(message: Message, state: FSMContext):
    await loggers[message.from_user.id].set_rating(message.text)
    await state.set_state(Form.comments)
    await message.answer("Thanks, any comments?")


@router.message(Form.comments)
async def final_message(message: Message, state: FSMContext):
    await loggers[message.from_user.id].set_comments(message.text)
    await loggers[message.from_user.id].print_df()
    await loggers[message.from_user.id].commit_log_entry()
    await state.clear()
    await message.answer("Thank you for your feedback! Feel free to ask me some more questions!")
    await cmd_start(message)


async def main() -> None:
    prepare_documents()
    bot = Bot(TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())