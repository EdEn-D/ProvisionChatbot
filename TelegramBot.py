import csv
import os
import logging
from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler

import TechSupportBot

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

modes = ["wfq", "thinking", "rating", "notes"]
mode = modes[0]

log_row = {
    "Query": "None",
    "Response": "None",
    "Rating": "None",
    "Notes": "None"
}


def push_log():
    global log_row
    file_exists = os.path.isfile("AI_bot_log.csv")

    with open("AI_bot_log.csv", mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=log_row.keys())

        if not file_exists:
            writer.writeheader()  # Write the headers if the file does not exist

        writer.writerow(log_row)  # Append the current log_row

    print(log_row.values())  # Print the values of log_row

    # Reset log_row to its default state
    log_row = {
        "Query": "None",
        "Response": "None",
        "Rating": "None",
        "Notes": "None"
    }

def mode_switch(force_mode=""):
    global mode
    print(f"mode before {mode}")
    index = modes.index(mode)
    mode = modes[(index+1)%len(modes)]
    print(f"mode after {mode}")


initial_keyboard = [
        [
            InlineKeyboardButton("Ask a question", callback_data="qa"),
            InlineKeyboardButton("Get training data", callback_data="get_data"),
        ]
    ]

response_rating_keyboard = [
    [
        InlineKeyboardButton("Correct answer", callback_data="correct"),
        InlineKeyboardButton("Incorrect answer", callback_data="incorrect"),
    ],
    [
        InlineKeyboardButton("Doesn't know :(", callback_data="idk"),
    ],
]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # reply_markup = InlineKeyboardMarkup(initial_keyboard)
    # await update.message.reply_text("Please choose:", reply_markup=reply_markup)

    # Other options:
    # await context.bot.send_message(text="Please choose:", reply_markup=reply_markup, chat_id=update.effective_chat.id)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Ask the AI questions then rate the response for training\n"
                                                                          "Use /getdata command to see which data I am trained on")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if mode == "notes":
        log_row["Notes"] = update.message.text
        print(f"Saving notes: {update.message.text}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Thank you! I am ready for the next question!")
        push_log()
        mode_switch()
        return

    if mode != "wfq":
        return
    mode_switch()

    # 1. Saving the question, logging and sending chat message to user
    log_row["Query"] = update.message.text
    print(f"sending question to AI bot: {update.message.text}")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Asking AI a question... Please wait")

    # 2. asking AI the question and saving the response, and sending chat message to user
    ai_response = TechSupportBot.invoke_prompt(update.message.text) # TODO: deal with async response
    log_row["Response"] = ai_response
    print(f"ai_response: {ai_response}")
    await context.bot.send_message(chat_id=update.effective_chat.id, text=ai_response)

    # 3. Ask for rating
    await ask_for_rating(update, context)
async def ask_for_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode_switch()
    reply_markup = InlineKeyboardMarkup(response_rating_keyboard)
    await update.message.reply_text("Please choose:", reply_markup=reply_markup) # Go to button function below

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()

    log_row["Rating"] = query.data
    print(f"Rating: {query.data}")
    await ask_for_notes(update, context)

async def ask_for_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode_switch()
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Notes: ")


async def ask_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Asking AI a question...")

async def get_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=TechSupportBot.get_embedded_data())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays info on how to use the bot."""
    await update.message.reply_text("Use /start to test this bot.")

if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    ## General Commands
    start_handler = CommandHandler('start', start)
    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    help_handler = CommandHandler("help", help_command)
    ask_ai_handler = CommandHandler("askai", ask_ai)
    get_data_handler = CommandHandler("getdata", get_data)

    application.add_handler(start_handler)
    application.add_handler(echo_handler)
    application.add_handler(help_handler)
    application.add_handler(ask_ai_handler)
    application.add_handler(get_data_handler)


    ## Buttons
    button_handler = CallbackQueryHandler(button)

    application.add_handler(button_handler)


    application.run_polling()