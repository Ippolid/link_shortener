import logging
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

START_CHOICES, REPLY_FOR_CREATE, URL_CHOICES, REPLY_FOR_DELETE = range(4)

create_url_btn = 'создать ссылку'
to_main_page_btn = 'на главную'
list_of_urls_btn = "список ссылок"

start_markups_keyboard = [
    [create_url_btn],
    [list_of_urls_btn],
]
start_markups = ReplyKeyboardMarkup(start_markups_keyboard, one_time_keyboard=True)

delete_url_btn = 'удалить ссылку'
change_url_btn = 'изменить срок действия ссылки'
to_main_page_btn = 'на главную'

urls_markups_keyboard = [
    [delete_url_btn],
    [change_url_btn],
    [to_main_page_btn],
]
urls_markups = ReplyKeyboardMarkup(urls_markups_keyboard, one_time_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "старт",
        reply_markup=start_markups,
    )

    return START_CHOICES


async def create_url_ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    context.user_data["choice"] = text
    await update.message.reply_text(f"введите ссылку")

    return REPLY_FOR_CREATE


async def create_url_get(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    response = 'http'

    await update.message.reply_text(
        f"ваша ссылка {response}",
        reply_markup=start_markups,
    )

    return START_CHOICES


async def list_of_urls(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    response = ['http', 'http']

    await update.message.reply_text(
        f"список ссылок {response}",
        reply_markup=urls_markups,
    )
    return URL_CHOICES


async def delete_url_ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    context.user_data["choice"] = text
    await update.message.reply_text(f"введите номер ссылки, которую удалить")

    return REPLY_FOR_DELETE


async def delete_url_get(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    response = 'okay'

    await update.message.reply_text(
        f"ваша ссылка {response}",
        reply_markup=start_markups,
    )

    return START_CHOICES


async def to_main_page(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        'start',
        reply_markup=start_markups,
        )
    return START_CHOICES

TOKEN = '7927553615:AAGSdUqicPUs3GIRRtjO3j7Fe29KDsdVdK0'


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            START_CHOICES: [
                MessageHandler(
                    filters.Regex(f"^({create_url_btn})$"), create_url_ask
                ),
                MessageHandler(
                    filters.Regex(f"^({list_of_urls_btn})$"), list_of_urls
                ),
            ],
            REPLY_FOR_CREATE: [
                MessageHandler(
                    filters.TEXT & ~(filters.COMMAND | filters.Regex(f"^({to_main_page_btn})$")),
                    create_url_get,
                ),
            ],
            URL_CHOICES: [
                MessageHandler(
                    filters.Regex(f"^({delete_url_btn})$"), delete_url_ask
                ),
                # MessageHandler(
                #     filters.Regex(f"^({change_url_btn})$"), change_url
                # ),
                MessageHandler(
                    filters.Regex(f"^({to_main_page_btn})$"), to_main_page
                ),
            ],
            REPLY_FOR_DELETE: [
                MessageHandler(
                    filters.TEXT & ~(filters.COMMAND | filters.Regex(f"^({to_main_page_btn})$")),
                    delete_url_get,
                ),
            ],
        },
        fallbacks=[MessageHandler(filters.Regex(f"^({to_main_page_btn})$"), to_main_page)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()