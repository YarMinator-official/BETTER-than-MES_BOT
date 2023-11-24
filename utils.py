from datetime import datetime
from telebot import types
from functools import lru_cache

WEEKDAYS = {
    0: "Понедельник",
    1: "Вторник",
    2: "Среда",
    3: "Четверг",
    4: "Пятница",
    5: "Суббота",
    6: "Воскресенье"
}
HW_ATTACHMENTS_URL = "[ссылка]({})"

def parse_schedule(obj):
    result = "\n"
    for item in enumerate(obj):
        marks = f"\nОценки за урок: <tg-spoiler> {", ".join(item[1].marks)} </tg-spoiler>" if item[1].marks else ""
        result += f"<b>{item[0]+1}. {item[1].subject_name}</b>, <code>к.{item[1].room_number}</code>\n{item[1].lesson_time}{marks}\n\n"
    return result

def parse_marks(obj):
    result = "\n"
    for item in obj:
        result += f"<b>{item.subject_name}</b>: {", ".join(item.values)}\n"
    return result

def parse_homework(obj):
    result = "\n"
    for item in enumerate(obj):
        files = f"\nФайл: {", ".join(item[1].attached_files)}" if item[1].attached_files else ""
        tests = f"\nТест(ы): {", ".join(item[1].attached_tests)}" if item[1].attached_tests else ""
        result += f"<b>{item[0]+1}. {item[1].subject_name}:</b>\n<code>{item[1].description}</code>{files}{tests}\n\n"
    return result

def parse_trimester(obj):
    result = ""
    for item in obj:
        result += f"<b>{item.subject_name}</b>\n<b>Средний балл - {item.average_mark}</b>\nОценки: {", ".join(item.values)}\n\n"
    return result

@lru_cache()
def convert_to_non_retarded_date(date2convert: str):
    date2convert = datetime.strptime(date2convert, "%Y-%m-%d")
    return f"{WEEKDAYS[datetime.weekday(date2convert)]}, \
{datetime.strftime(date2convert, "%d/%m/%Y")}"

@lru_cache()
def convert_date_format(datef: datetime.date):
    return f"{WEEKDAYS[datetime.weekday(datef)]}, \
{datetime.strftime(datef, "%d/%m/%Y")}"

def create_inline_kb(callback_data):
    kb = types.InlineKeyboardMarkup()
    next_button = types.InlineKeyboardButton(text="->", callback_data=f"next_{callback_data}")
    prev_button = types.InlineKeyboardButton(text="<-", callback_data=f"prev_{callback_data}")
    kb.add(prev_button, next_button)
    return kb

def create_trimester_inline():
    trimester_kb = types.InlineKeyboardMarkup()
    a = types.InlineKeyboardButton(text="1️⃣", callback_data=f"TRIMESTER_1")
    b = types.InlineKeyboardButton(text="2️⃣", callback_data=f"TRIMESTER_2")
    c = types.InlineKeyboardButton(text="3️⃣", callback_data=f"TRIMESTER_3")
    trimester_kb.add(a, b, c)
    return trimester_kb
