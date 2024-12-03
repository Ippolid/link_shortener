from dotenv import load_dotenv
import os
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
load_dotenv()  # take environment variables from .env.
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
TOKEN = os.getenv('TOKEN')
START_CHOICES, REPLY_FOR_CREATE, URL_CHOICES, REPLY_FOR_DELETE, \
REPLY_FOR_CHANGE, ASK_FOR_PERIOD, REPLY_FOR_CHANGE_PERIOD = range(7)

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
    response = ['http_1', 'http_2']
    user_data = context.user_data
    if not user_data.get('urls'):
        user_data['urls'] = response
    urls = user_data['urls']
    urls_str = ''
    for i in range(len(urls)):
        urls_str += f"\n{i + 1} {urls[i]}"
    await update.message.reply_text(
        f"список ссылок {urls_str}",
        reply_markup=urls_markups,
    )
    return URL_CHOICES


async def delete_url_ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(f"введите номер ссылки, которую удалить")

    return REPLY_FOR_DELETE


async def delete_url_get(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    user_data = context.user_data
    user_data['urls'].pop(int(text) - 1)
    print(user_data['urls'])
    response = '200_OK'

    await update.message.reply_text(
        f"удаление ссылки: {response}",
        reply_markup=urls_markups,
    )

    return URL_CHOICES


async def change_url_ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    context.user_data["choice"] = text
    await update.message.reply_text(f"введите номер ссылки, срок действия которой хотите изменить")

    return REPLY_FOR_CHANGE


async def change_url_get(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    response = ['http', '30 дней']
    await update.message.reply_text(
        f"ваша ссылка {response[0]}, срок действия {response[1]}"
    )
    await update.message.reply_text(
        'Введите новый срок действия в днях',
        reply_markup=urls_markups,
    )

    return REPLY_FOR_CHANGE_PERIOD

#
# async def change_url_period_ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     # text = update.message.text
#     # context.user_data["choice"] = text
#     await update.message.reply_text(f"введите желаемый срок действия")
#
#     return REPLY_FOR_CHANGE_PERIOD


async def change_url_period_get(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    response = '200_OK'
    new_period = update.message.text
    await update.message.reply_text(
        f'ответ: {response}, новый срок действия: {new_period}',
        reply_markup=urls_markups,
    )

    return URL_CHOICES


async def to_main_page(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        'start',
        reply_markup=start_markups,
    )
    return START_CHOICES


def main() -> None:
    application = Application.builder().token(TOKEN).build()

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
                MessageHandler(
                    filters.Regex(f"^({change_url_btn})$"), change_url_ask
                ),
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
            REPLY_FOR_CHANGE: [
                MessageHandler(
                    filters.TEXT & ~(filters.COMMAND | filters.Regex(f"^({to_main_page_btn})$")),
                    change_url_get,
                ),
            ],
            # ASK_FOR_PERIOD: [
            #     MessageHandler(
            #         filters.TEXT & ~(filters.COMMAND | filters.Regex(f"^({to_main_page_btn})$")),
            #         change_url_period_get,
            #     ),
            # ],
            REPLY_FOR_CHANGE_PERIOD: [
                MessageHandler(
                    filters.TEXT & ~(filters.COMMAND | filters.Regex(f"^({to_main_page_btn})$")),
                    change_url_period_get,
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
