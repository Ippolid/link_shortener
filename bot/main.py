from dotenv import load_dotenv
import os
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters, CallbackQueryHandler,
)
import calendar
from datetime import datetime, timedelta
import httpx

load_dotenv()  # take environment variables from .env.

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
TOKEN = os.getenv('TOKEN')
BASE_URL = os.getenv('BASE_URL')

START_CHOICES, REPLY_FOR_CREATE, URL_CHOICES, REPLY_FOR_DELETE, \
REPLY_FOR_CHANGE, ASK_FOR_PERIOD, REPLY_FOR_CHANGE_PERIOD, CHANGE_PERIOD_30, \
URL_EVENTS, DELETE_LINK_YES = range(10)

create_url_btn = 'создание 🔗'
list_of_urls_btn = "список"

delete_url_btn = 'удаление'
change_url_btn = 'изменить срок действия'
to_main_page_btn = 'на главную'

to_main_page_button = [
    [
        InlineKeyboardButton(text=to_main_page_btn, callback_data=str(URL_CHOICES)),
    ]
]
keyboard_to_main_page = InlineKeyboardMarkup(to_main_page_button)

create_button = [
    [
        InlineKeyboardButton(text=create_url_btn, callback_data=str(REPLY_FOR_CREATE)),
    ],
]
create_keyboard = InlineKeyboardMarkup(create_button)

urls_buttons = [
    [
        InlineKeyboardButton(text=delete_url_btn, callback_data=str(REPLY_FOR_DELETE)),
        InlineKeyboardButton(text=to_main_page_btn, callback_data=str(URL_CHOICES)),
    ],
    [
        InlineKeyboardButton(text=change_url_btn, callback_data=str(REPLY_FOR_CHANGE)),
        InlineKeyboardButton(text="продлить на 30 дней", callback_data=str(CHANGE_PERIOD_30)),
    ]
]
urls_keyboard = InlineKeyboardMarkup(urls_buttons)


def return_to_main_page_after_error(update, msg):
    update.callback_query.edit_message_text(
        f"{msg}, попробуйте позже",
        reply_markup=keyboard_to_main_page,
    )
    return URL_CHOICES


def get_month_name(month_no, ):
    with calendar.different_locale("ru_RU.UTF-8"):
        month_name = calendar.month_name[month_no]
        return month_name


def date_to_rus_with_month(date: datetime.date):
    return f"{date.day} {get_month_name(date.month)} {date.year}"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        response = httpx.get(
            f"{BASE_URL}/statistic/{user_id}"
        )
        response.raise_for_status()
    except Exception as ex:
        return return_to_main_page_after_error(update, "Не удалось получить список ссылок")

    urls = response.json()["links"]
    if urls.keys():
        button_list = []
        for url_short, url_long in urls.items():
            button_list.append(InlineKeyboardButton(url_long, callback_data=f"url_is_{url_short}"))
        dynamic_buttons = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
        dynamic_buttons.append(create_button[0])
        urls_keyboard_dynamic = InlineKeyboardMarkup(dynamic_buttons)

        await update.message.reply_text(
            f"Ваши ссылки:",
            reply_markup=urls_keyboard_dynamic,
        )
        return URL_CHOICES

    else:
        await update.message.reply_text(
            "Уважаемый пользователь, Вас приветствует бот по созданию коротких ссылок!",
            reply_markup=create_keyboard,
        )
        return START_CHOICES


async def create_url_ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.effective_message.edit_text(
        "Введите свою ссылку:",
    )
    return REPLY_FOR_CREATE


async def create_url_get(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    old_url = update.message.text

    response = None
    try:
        response = httpx.get(old_url)
        response.raise_for_status()
    except Exception as ex:
        if response and response.status_code == 301:
            await update.message.reply_markdown(
                f"Вы ввели ссылку, которая не является конечной.\n"
                f"Попробуйте вставить эту ссылку в браузер и записать здесь новый результат после её загрузки\n",
                reply_markup=keyboard_to_main_page,
            )
            return REPLY_FOR_CREATE
        else:
            await update.message.reply_markdown(
                f"Вы ввели нерабочую ссылку.\n"
                f"Обратите внимание, что ссылка должна начинаться с `https://` или `http://`\n",
                reply_markup=keyboard_to_main_page,
            )
            return REPLY_FOR_CREATE

    try:
        response = httpx.post(
            f"{BASE_URL}/url",
            json={
                "oldurl": old_url,
                "userid": str(user_id),
            }
        )
        response.raise_for_status()
    except Exception as ex:
        await return_to_main_page_after_error(update, "Не удалось создать ссылку")

    short_url = response.json()["shorturl"]
    await update.message.reply_markdown(
        f"Ваша ссылка ```{short_url}```",
        reply_markup=keyboard_to_main_page,
    )

    return START_CHOICES


async def list_of_urls(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    response = None
    try:
        response = httpx.get(
            f"{BASE_URL}/statistic/{user_id}"
        )
        response.raise_for_status()
    except Exception as ex:
        await return_to_main_page_after_error(update, "Не удалось получить список ссылок")

    urls = response.json()["links"]
    if urls.keys():
        button_list = []
        for url_short, url_long in urls.items():
            button_list.append(InlineKeyboardButton(url_long, callback_data=f"url_is_{url_short}"))
        dynamic_buttons = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
        dynamic_buttons.append(create_button[0])
        urls_keyboard_dynamic = InlineKeyboardMarkup(dynamic_buttons)

        await update.callback_query.edit_message_text(
            f"Ваши ссылки",
            reply_markup=urls_keyboard_dynamic,
        )

    else:
        await update.effective_message.edit_text(
            "На данный момент у Вас нет активных ссылок",
            reply_markup=create_keyboard,
        )

    return URL_CHOICES


async def url_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    url_id = update.callback_query.data[7:]
    user_id = update.effective_user.id

    response = None
    try:
        response = httpx.get(
            f"{BASE_URL}/statistic/{user_id}/{url_id}"
        )
        response.raise_for_status()
    except Exception as ex:
        await return_to_main_page_after_error(update, "Не удалось получить информацию по ссылке")

    url_info = response.json()
    short_url = f"{BASE_URL}/{url_id}"
    long_url = url_info['link']
    transfer_count = url_info['transferCount']

    expire_time = datetime.strptime(url_info['expiretime'], '%Y-%m-%dT%H:%M:%SZ')
    expire_time_ru = f"{expire_time.day} {get_month_name(expire_time.month)} {expire_time.year} {expire_time.hour}:{expire_time.minute}"
    expire_time_delta = (expire_time - datetime.now()).days
    expire_info = ""
    if expire_time_delta < 0:
        expire_info = f"Срок действия истек {abs(expire_time_delta)} дней назад."
    elif expire_time_delta == 0:
        expire_info = f"Срок действия истекает меньше чем через сутки ({expire_time_ru})."
    elif expire_time_delta > 0:
        expire_info = f"Срок действия истекает через {expire_time_delta} дня ({expire_time_ru})."

    await update.callback_query.edit_message_text(
        f"Длинная ссылка:\n"
        f"{long_url}\n"
        f"Короткая ссылка:\n"
        f"{short_url}/\n"
        f"{expire_info}\n"
        f"Кол-во переходов: {transfer_count}\n",
        reply_markup=urls_keyboard,
    )
    context.user_data["link"] = {
        "short_link_id": url_id,
        "short_link": short_url,
        "long_link": long_url,
        "expire_time": expire_time,
        "transfer_count": transfer_count
    }
    return URL_EVENTS


async def delete_url_ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    current_long_link = context.user_data["link"]["long_link"]
    buttons = [
        [
            InlineKeyboardButton(text="Да", callback_data=str(DELETE_LINK_YES)),
            InlineKeyboardButton(text="Нет", callback_data=str(URL_CHOICES)),
        ]
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    await update.callback_query.edit_message_text(
        f"Вы уверены, что хотите удалить ссылку?\n "
        f"{current_long_link}",
        reply_markup=keyboard,
    )
    return REPLY_FOR_DELETE


async def delete_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    current_link_id = context.user_data["link"]['short_link_id']
    user_id = update.effective_user.id
    try:
        response = httpx.delete(
            f"{BASE_URL}/{user_id}/delete/{current_link_id}",
        )
        response.raise_for_status()
    except Exception as ex:
        await return_to_main_page_after_error(update, "Не удалось удалить ссылку, попробуйте позже")

    await update.callback_query.edit_message_text(
        f"Ссылка успешно удалена\n",
        reply_markup=keyboard_to_main_page,
    )
    return START_CHOICES


async def change_url_ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.edit_message_text(
        'Введите новый срок действия в часах',
    )
    return REPLY_FOR_CHANGE_PERIOD


async def change_url_period_get(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        assert update.message.text.isdigit()
        expire_delta = int(update.message.text)
    except Exception as ex:
        await update.message.reply_text(
            f"Не удалось обработать данные. Срок действия должен быть целым числом и больше 0",
        )
        return REPLY_FOR_CHANGE

    current_link_id = context.user_data["link"]['short_link_id']
    user_id = update.effective_user.id

    try:
        response = httpx.put(
            f"{BASE_URL}/{user_id}/change/{current_link_id}/{expire_delta}",
        )
        response.raise_for_status()
    except Exception as ex:
        await return_to_main_page_after_error(update, "Не удалось продлить срок действия")

    new_expire_time = datetime.now() + timedelta(hours=expire_delta)
    expire_time_ru = f"{new_expire_time.day} {get_month_name(new_expire_time.month)} {new_expire_time.year} {new_expire_time.hour}:{new_expire_time.minute}"

    await update.message.reply_text(
        f"Срок действия ссылки установлен до {expire_time_ru}",
        reply_markup=keyboard_to_main_page,
    )
    return START_CHOICES


async def change_url_period_30(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    expire_delta_to_add = 30 * 24
    current_link_id = context.user_data["link"]['short_link_id']
    user_id = update.effective_user.id
    try:
        expire_delta = (context.user_data["link"]['expire_time'] - datetime.now()).days * 24
        response = httpx.put(
            f"{BASE_URL}/{user_id}/change/{current_link_id}/{expire_delta + expire_delta_to_add}",
        )
        response.raise_for_status()
    except Exception as ex:
        await return_to_main_page_after_error(update, "Не удалось продлить срок действия")

    new_expire_time = datetime.now() + timedelta(hours=expire_delta + expire_delta_to_add)
    expire_time_ru = f"{new_expire_time.day} {get_month_name(new_expire_time.month)} {new_expire_time.year}"

    await update.callback_query.edit_message_text(
        f"Срок действия ссылки установлен до {expire_time_ru}",
        reply_markup=keyboard_to_main_page,
    )
    return START_CHOICES


def main() -> None:
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            START_CHOICES: [
                CallbackQueryHandler(create_url_ask, pattern="^" + str(REPLY_FOR_CREATE) + "$"),
                CallbackQueryHandler(url_edit, pattern="^url_is"),
            ],
            REPLY_FOR_CREATE: [
                MessageHandler(
                    filters.TEXT & ~(filters.COMMAND | filters.Regex(f"^({to_main_page_btn})$")),
                    create_url_get,
                ),
            ],
            URL_CHOICES: [
                CallbackQueryHandler(url_edit, pattern="^url_is"),
                CallbackQueryHandler(create_url_ask, pattern="^" + str(REPLY_FOR_CREATE) + "$"),
            ],
            URL_EVENTS: [
                CallbackQueryHandler(delete_url_ask, pattern="^" + str(REPLY_FOR_DELETE) + "$"),
                CallbackQueryHandler(change_url_ask, pattern="^" + str(REPLY_FOR_CHANGE) + "$"),
                CallbackQueryHandler(change_url_period_30, pattern="^" + str(CHANGE_PERIOD_30) + "$"),
            ],
            REPLY_FOR_DELETE: [
                CallbackQueryHandler(delete_url, pattern="^" + str(DELETE_LINK_YES) + "$"),
                CallbackQueryHandler(list_of_urls, pattern="^" + str(URL_CHOICES) + "$"),
            ],
            REPLY_FOR_CHANGE_PERIOD: [
                MessageHandler(
                    filters.TEXT & ~(filters.COMMAND | filters.Regex(f"^({to_main_page_btn})$")),
                    change_url_period_get,
                ),
            ],
        },
        fallbacks=[CallbackQueryHandler(list_of_urls, pattern="^" + str(URL_CHOICES) + "$")]
    )

    application.add_handler(conv_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()