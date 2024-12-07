from dotenv import load_dotenv
import os
import logging
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters, CallbackQueryHandler,
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
list_of_urls_btn = "список ссылок"

delete_url_btn = 'удалить ссылку'
change_url_btn = 'изменить срок действия ссылки'
to_main_page_btn = 'на главную'

urls_markups_keyboard = [
    [delete_url_btn],
    [change_url_btn],
    [to_main_page_btn],
]
urls_markups = ReplyKeyboardMarkup(urls_markups_keyboard, one_time_keyboard=True)

start_buttons = [
    [
        InlineKeyboardButton(text=create_url_btn, callback_data=str(REPLY_FOR_CREATE)),
        InlineKeyboardButton(text=list_of_urls_btn, callback_data=str(URL_CHOICES)),
    ],
]
start_keyboard = InlineKeyboardMarkup(start_buttons)

urls_buttons = [
    [
        InlineKeyboardButton(text=delete_url_btn, callback_data=str(REPLY_FOR_DELETE)),
        InlineKeyboardButton(text=change_url_btn, callback_data=str(REPLY_FOR_CHANGE)),
        InlineKeyboardButton(text=to_main_page_btn, callback_data=str(START_CHOICES)),
    ],
]
urls_keyboard = InlineKeyboardMarkup(urls_buttons)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Уважаемый пользователь, Вас приветствует бот по созданию коротких ссылок! Выберите один из вариантов",
        reply_markup=start_keyboard,
    )

    return START_CHOICES


async def create_url_ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.effective_message.edit_text(
        "Введите свою ссылку",
    )
    return REPLY_FOR_CREATE


async def create_url_get(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    response = 'https://google.com'

    await update.message.reply_markdown(
        f"Ваша ссылка ```{response}```",
        reply_markup=start_keyboard,
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
    await update.callback_query.edit_message_text(
        f"список ссылок {urls_str}",
        reply_markup=urls_keyboard,
    )
    return URL_CHOICES


async def delete_url_ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.effective_message.edit_text(f"введите номер ссылки, которую удалить")

    return REPLY_FOR_DELETE


async def delete_url_get(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    user_data = context.user_data
    user_data['urls'].pop(int(text) - 1)
    print(user_data['urls'])
    response = '200_OK'

    urls = user_data['urls']
    urls_str = ''
    for i in range(len(urls)):
        urls_str += f"\n{i + 1} {urls[i]}"

    await update.message.reply_text(
        f"Удаление ссылки: {response}\n"
        f"Список ссылок {urls_str}",
        reply_markup=urls_keyboard,
    )

    return URL_CHOICES


async def change_url_ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.effective_message.edit_text(f"Введите номер ссылки, срок действия которой хотите изменить")

    return REPLY_FOR_CHANGE


async def change_url_get(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    response = ['http', '30 дней']
    await update.message.reply_text(
        f"ваша ссылка {response[0]}, срок действия {response[1]}"
    )
    await update.message.reply_text(
        'Введите новый срок действия в днях',
    )

    return REPLY_FOR_CHANGE_PERIOD


async def change_url_period_get(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    response = '200_OK'
    new_period = update.message.text

    user_data = context.user_data
    urls = user_data['urls']
    urls_str = ''
    for i in range(len(urls)):
        urls_str += f"\n{i + 1} {urls[i]}"

    await update.message.reply_text(
        f'Ответ: {response}, новый срок действия: {new_period}\n'
        f"Список ссылок {urls_str}",
        reply_markup=urls_keyboard,
    )

    return URL_CHOICES


async def to_main_page(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.edit_message_text(
        'Выберите один из вариантов',
        reply_markup=start_keyboard,
    )
    return START_CHOICES


def main() -> None:
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            START_CHOICES: [
                CallbackQueryHandler(create_url_ask, pattern="^" + str(REPLY_FOR_CREATE) + "$"),
                CallbackQueryHandler(list_of_urls, pattern="^" + str(URL_CHOICES) + "$"),
            ],
            REPLY_FOR_CREATE: [
                MessageHandler(
                    filters.TEXT & ~(filters.COMMAND | filters.Regex(f"^({to_main_page_btn})$")),
                    create_url_get,
                ),
            ],
            URL_CHOICES: [
                CallbackQueryHandler(delete_url_ask, pattern="^" + str(REPLY_FOR_DELETE) + "$"),
                CallbackQueryHandler(change_url_ask, pattern="^" + str(REPLY_FOR_CHANGE) + "$"),
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
            REPLY_FOR_CHANGE_PERIOD: [
                MessageHandler(
                    filters.TEXT & ~(filters.COMMAND | filters.Regex(f"^({to_main_page_btn})$")),
                    change_url_period_get,
                ),
            ],
        },
        fallbacks=[CallbackQueryHandler(to_main_page, pattern="^" + str(START_CHOICES) + "$")]
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
