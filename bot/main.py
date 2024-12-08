from dotenv import load_dotenv
import os
import json
import logging
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters, CallbackQueryHandler, CallbackContext,
)
import httpx

load_dotenv()  # take environment variables from .env.
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
TOKEN = os.getenv('TOKEN')
BASE_URL = os.getenv('BASE_URL')

START_CHOICES, REPLY_FOR_CREATE, URL_CHOICES, REPLY_FOR_DELETE, \
REPLY_FOR_CHANGE, ASK_FOR_PERIOD, REPLY_FOR_CHANGE_PERIOD, \
URL_EVENTS, DELETE_LINK_YES = range(9)

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
    user_id = update.effective_user.id
    response = httpx.post(
        f"{BASE_URL}/url",
        json={
            "oldurl": update.message.text,
            "userid": str(user_id),
        }
    )
    if response.status_code != 200:
        await update.message.reply_text(
            f"Не удалось создать ссылку. Подробности {response.text}",
            reply_markup=start_keyboard,
        )
        return START_CHOICES

    short_url = response.json()["shorturl"]
    await update.message.reply_markdown(
        f"Ваша ссылка ```{short_url}```",
        reply_markup=start_keyboard,
    )

    return START_CHOICES


async def list_of_urls(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    try:
        response = httpx.get(
            f"{BASE_URL}/statistic/{user_id}"
        )
        response.raise_for_status()
    except Exception as ex:
        await update.callback_query.edit_message_text(
            f"Не удалось получить список ссылок. Подробности {ex}",
            reply_markup=start_keyboard,
        )
        return START_CHOICES

    urls = response.json()["links"]

    button_list = []
    for url in urls:
        button_list.append(InlineKeyboardButton(url, callback_data=f"url_is_{url}"))
    urls_keyboard_dynamic = InlineKeyboardMarkup(
        [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
    )  # 1 is for single column and mutliple rows

    user_data = context.user_data
    if not user_data.get('urls'):
        user_data['urls'] = urls
    urls = user_data['urls']
    urls_str = ''
    for i in range(len(urls)):
        urls_str += f"\n{i + 1} {urls[i]}"
    await update.callback_query.edit_message_text(
        f"список ссылок {urls_str}",
        reply_markup=urls_keyboard_dynamic,
    )
    return URL_CHOICES


async def url_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    url_id = update.callback_query.data[8:]
    user_id = update.effective_user.id
    try:
        response = httpx.get(
            f"{BASE_URL}/statistic/{user_id}/{url_id}"
        )
    except Exception as ex:
        await update.message.reply_text(
            f"Не удалось получить информацию по ссылке. Подробности {ex}",
            reply_markup=start_keyboard,
        )
        return START_CHOICES

    url_info = response.json()

    await update.callback_query.edit_message_text(
        f"Длинная ссылка:\n "
        f"{url_info}\n"
        f"Короткая ссылка:\n"
        f"{url_info}",
        reply_markup=urls_keyboard,
    )
    context.user_data["link"] = {
        "short_link": url_info,
        "long_link": url_info,
        "date_expired": url_info
    }

    return URL_EVENTS


async def delete_url_ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    current_link = context.user_data["link"]
    buttons = [
        [
            InlineKeyboardButton(text="Да", callback_data=str(DELETE_LINK_YES)),
            InlineKeyboardButton(text="Нет", callback_data=str(START_CHOICES)),
        ]
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    await update.callback_query.edit_message_text(
        f"Вы уверены, что хотите удалить ссылку?\n "
        f"Длинная ссылка:\n "
        f"{current_link}\n"
        f"Короткая ссылка:\n"
        f"{current_link}",
        reply_markup=keyboard,
    )

    return REPLY_FOR_DELETE


async def delete_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    current_link = context.user_data["link"]
    response = httpx.delete()

    await update.callback_query.edit_message_text(
        f"Ссылка успешно удалена\n "
        f"Длинная ссылка:\n "
        f"{current_link}\n"
        f"Короткая ссылка:\n"
        f"{current_link}",
        reply_markup=start_keyboard,
    )

    return START_CHOICES


async def change_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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
                CallbackQueryHandler(url_edit, pattern="^url_is"),
            ],
            URL_EVENTS: [
                CallbackQueryHandler(delete_url_ask, pattern="^" + str(REPLY_FOR_DELETE) + "$"),
                CallbackQueryHandler(change_url, pattern="^" + str(REPLY_FOR_CHANGE) + "$"),
            ],
            REPLY_FOR_DELETE: [
                CallbackQueryHandler(delete_url, pattern="^" + str(REPLY_FOR_DELETE) + "$"),
                CallbackQueryHandler(delete_url, pattern="^" + str(START_CHOICES) + "$"),
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
