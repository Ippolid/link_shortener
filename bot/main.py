from dotenv import load_dotenv
import os
import logging
from telegram import ReplyKeyboardMarkup, Update, InlineKeyboardMarkup, InlineKeyboardButton
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

create_url_btn = 'создать ссылку'
list_of_urls_btn = "список ссылок"

delete_url_btn = 'удалить ссылку'
change_url_btn = 'изменить срок действия'
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
        InlineKeyboardButton(text=to_main_page_btn, callback_data=str(START_CHOICES)),
    ],
    [
        InlineKeyboardButton(text=change_url_btn, callback_data=str(REPLY_FOR_CHANGE)),
        InlineKeyboardButton(text="продлить на 30 дней", callback_data=str(CHANGE_PERIOD_30)),
    ]
]
urls_keyboard = InlineKeyboardMarkup(urls_buttons)


def get_month_name(month_no, ):
    with calendar.different_locale("ru_RU.UTF-8"):
        month_name = calendar.month_name[month_no]
        return month_name


def date_to_rus_with_month(date: datetime.date):
    return f"{date.day} {get_month_name(date.month)} {date.year}"


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
    if urls.keys():
        button_list = []
        for url_short, url_long in urls.items():
            button_list.append(InlineKeyboardButton(url_long, callback_data=f"url_is_{url_short}"))
        urls_keyboard_dynamic = InlineKeyboardMarkup(
            [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
        )

        await update.callback_query.edit_message_text(
            f"Ваши ссылки",
            reply_markup=urls_keyboard_dynamic,
        )
        return URL_CHOICES

    else:
        await update.effective_message.edit_text(
            "Ничего не найдено. Попробуйте ввести свою первую ссылку ниже:",
        )
        return REPLY_FOR_CREATE


async def url_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    url_id = update.callback_query.data[7:]
    user_id = update.effective_user.id
    user_id = 1264944693
    try:
        response = httpx.get(
            f"{BASE_URL}/statistic/{user_id}/{url_id}"
        )
        response.raise_for_status()
    except Exception as ex:
        await update.message.reply_text(
            f"Не удалось получить информацию по ссылке. Подробности {ex}",
            reply_markup=start_keyboard,
        )
        return START_CHOICES

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
            InlineKeyboardButton(text="Нет", callback_data=str(START_CHOICES)),
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
    user_id = 1264944693
    try:
        response = httpx.delete(
            f"{BASE_URL}/{user_id}/delete/{current_link_id}",
        )
        response.raise_for_status()
    except Exception as ex:
        await update.message.reply_text(
            f"Не удалось удалить ссылку. Подробности: {ex}",
            reply_markup=start_keyboard,
        )
        return START_CHOICES

    await update.callback_query.edit_message_text(
        f"Ссылка успешно удалена\n",
        reply_markup=start_keyboard,
    )

    return START_CHOICES


async def change_url_ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.edit_message_text(
        'Введите новый срок действия в часах',
    )

    return REPLY_FOR_CHANGE_PERIOD


async def change_url_period_get(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        expire_delta = int(update.message.text)
    except Exception as ex:
        await update.message.reply_text(
            f"Не удалось обработать данные. Введите, пожалуйста, число:",
        )
        return REPLY_FOR_CHANGE

    current_link_id = context.user_data["link"]['short_link_id']
    user_id = update.effective_user.id
    user_id = 1264944693

    try:
        response = httpx.put(
            f"{BASE_URL}/{user_id}/change/{current_link_id}/{expire_delta}",
        )
        response.raise_for_status()
    except Exception as ex:
        await update.message.reply_text(
            f"Не удалось продлить срок действия. Подробности: {ex}",
            reply_markup=start_keyboard,
        )
        return START_CHOICES

    new_expire_time = datetime.now() + timedelta(hours=expire_delta)
    expire_time_ru = f"{new_expire_time.day} {get_month_name(new_expire_time.month)} {new_expire_time.year} {new_expire_time.hour}:{new_expire_time.minute}"

    await update.message.reply_text(
        f"Срок действия ссылки установлен до {expire_time_ru}",
        reply_markup=start_keyboard,
    )

    return START_CHOICES


async def change_url_period_30(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    expire_delta_to_add = 30 * 24
    current_link_id = context.user_data["link"]['short_link_id']
    user_id = update.effective_user.id
    user_id = 1264944693
    try:
        expire_delta = (context.user_data["link"]['expire_time'] - datetime.now()).days * 24
        response = httpx.put(
            f"{BASE_URL}/{user_id}/change/{current_link_id}/{expire_delta + expire_delta_to_add}",
        )
        response.raise_for_status()
    except Exception as ex:
        await update.message.reply_text(
            f"Не удалось продлить срок действия. Подробности: {ex}",
            reply_markup=start_keyboard,
        )
        return START_CHOICES

    new_expire_time = datetime.now() + timedelta(hours=expire_delta + expire_delta_to_add)
    expire_time_ru = f"{new_expire_time.day} {get_month_name(new_expire_time.month)} {new_expire_time.year}"

    await update.callback_query.edit_message_text(
        f"Срок действия ссылки установлен до {expire_time_ru}",
        reply_markup=start_keyboard,
    )

    return START_CHOICES


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
        fallbacks=[CallbackQueryHandler(to_main_page, pattern="^" + str(START_CHOICES) + "$")]
    )

    application.add_handler(conv_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
