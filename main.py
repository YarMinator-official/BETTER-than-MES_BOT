import telebot
import school_mos
import logging

from telebot.apihelper import ApiTelegramException
from utils import *
from school_mos.errors import *
from threading import Thread
from datetime import date, timedelta

TOKEN = ""
bot = telebot.TeleBot(TOKEN, skip_pending=True, parse_mode="HTML", disable_web_page_preview=True)

logger = telebot.logger
telebot.logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(name)s-[%(asctime)s: %(levelname)s]")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

today_date = date.today()

schedule_inline = create_inline_kb("schedule")
marks_inline = create_inline_kb("marks")
homework_inline = create_inline_kb("homework")
trimester_marks_inline = create_trimester_inline()

users_dict = {}
date_offsets = {}

def clear_up_the_data():
    date_offsets = 0

@bot.message_handler(commands=["start"])
def welcome(message):
    global chat_id
    chat_id = message.chat.id
    bot.send_message(message.chat.id, "👋")
    bot.send_message(message.chat.id, f"Привет, <b>{(message.from_user.full_name)}</b>! Я МЭШ БОТ, твой личный помощник в мире с медленным сайтом МЭШ ;)")
    bot.send_message(message.chat.id, f"Для начала работы необходимо авторизоваться c данными от mos.ru.\n\nВоспользуйтесь командой /auth и следуйте указаниям.\n\n<b>Двухфакторная аутентификация должна быть отключена.</b>")

@bot.message_handler(commands=["auth"])
def auth_new_user(message):
    global auth_message
    user = users_dict.get(message.from_user.id)
    if user is not None:
        bot.send_message(message.chat.id, "Вы уже авторизованы! Для выхода из системы отправьте /logout.")
        return
    bot.send_message(message.chat.id, "Введите логин:")
    bot.register_next_step_handler(message, login_state)
    auth_message = message.id

def login_state(message):
    global login
    login = message.text
    bot.send_message(message.chat.id, "Введите пароль:")
    bot.register_next_step_handler(message, password_state)

def password_state(message):
    bot.send_message(message.chat.id, "⌛️")
    bot.send_message(message.chat.id, "Подождите, идёт авторизация...")
    Thread(target=send_welcome, args=(message, )).start()

@bot.message_handler(commands=["logout"])
def logout(message):
    user = users_dict.get(message.from_user.id)
    if user is None:
        bot.send_message(message.chat.id, "Вы не авторизованы!")
        return
    else:
        del users_dict[message.from_user.id]
        bot.send_message(message.chat.id, "Успешный выход из системы!")

def send_welcome(message):
    try:
        u_id = message.from_user.id
        users_dict[u_id] = school_mos.AUTH(login, message.text)
        date_offsets[u_id] = 0
        user = users_dict[message.from_user.id]
        bot.send_message(message.chat.id, f"Добро пожаловать в систему, <b>{user.first_name} {user.last_name}</b>!")
        bot.send_message(message.chat.id, "Используйте меню команд для нахождения нужных функций.")
    except InvalidCredentialsError:
        bot.send_message(message.chat.id, "Неверно указаны данные, либо у Вас включена двухфакторная аутентификация.\nПопробуйте снова!")
    except RequestError as RE:
        bot.send_message(message.chat.id, RE)

@bot.message_handler(commands=["profile"])
def user_profile(message):
    user = users_dict.get(message.from_user.id)
    if user is None:
        bot.send_message(message.chat.id, "Вы не авторизованы!")
        return
    user_prof = (f"{user.last_name} {user.first_name} {user.middle_name}\n\n<b>Рождён</b>: {convert_to_non_retarded_date(user.birth_date)}\n<b>Родитель(и)</b>: {", ".join(user.parents)}\n<b>СНИЛС</b>: {user.snils}\n\n<b>{user.user_school}, {user.class_name} класс</b>")
    bot.send_message(message.chat.id, f"<b>Профиль пользователя:</b>\n{user_prof}\n")

date2send = convert_to_non_retarded_date(str(today_date))

@bot.message_handler(commands=["schedule"])
def send_schedule(message):
    u_id = message.from_user.id
    user = users_dict.get(u_id)
    if user is None:
        bot.send_message(message.chat.id, "Вы не авторизованы!")
        return
    date_offsets[u_id] = 0
    try:
        raw_schedule = user.schedule.get_by_date()
        text = parse_schedule(raw_schedule)
    except (RequestError, NullFieldError):
        text = "На указанную дату ничего не найдено!"
    bot.send_message(message.chat.id, f"{date2send}\n{text}", reply_markup=schedule_inline)

@bot.message_handler(commands=["trimester"])
def send_trimestr_marks(message):
    user = users_dict.get(message.from_user.id)
    if user is None:
        bot.send_message(message.chat.id, "Вы не авторизованы!")
        return
    raw_trimestr_marks = user.marks.get_per_trimester()
    if raw_trimestr_marks is None:
        bot.send_message(message.chat.id, "У Вас нет оценок за аттестационные периоды!")
    else:
        text = parse_trimester(raw_trimestr_marks)
        bot.send_message(message.chat.id, f"Аттестационный период 1\n\n{text}", reply_markup=trimester_marks_inline)

@bot.message_handler(commands=["homework"])
def send_hw(message):
    u_id = message.from_user.id
    user = users_dict.get(u_id)
    if user is None:
        bot.send_message(message.chat.id, "Вы не авторизованы!")
        return
    date_offsets[u_id] = 0
    try:
        raw_hw = user.homework.get_by_date(0)
        text = parse_homework(raw_hw)
    except (RequestError, NullFieldError):
        text = "На указанную дату ничего не найдено!"
    bot.send_message(message.chat.id, f"{date2send}\n{text}", reply_markup=homework_inline)

@bot.message_handler(commands=["marks"])
def send_marks(message):
    u_id = message.from_user.id
    user = users_dict.get(u_id)
    if user is None:
        bot.send_message(message.chat.id, "Вы не авторизованы!")
        return
    date_offsets[u_id] = 0
    try:
        raw_marks = user.marks.get_by_date()
        text = parse_marks(raw_marks)
    except (RequestError, NullFieldError):
        text = "На указанную дату ничего не найдено!"
    bot.send_message(message.chat.id, f"{date2send}\n{text}", reply_markup=marks_inline)

@bot.callback_query_handler(lambda call: call.data.startswith("next") or call.data.startswith("prev"))
def callback_handler(call):
    u_id = call.from_user.id
    call_args = call.data.split("_")
    if call_args[0] == "next":
        date_offsets[u_id] += 1
    else:
        date_offsets[u_id] -= 1
    date_offset = date_offsets[u_id]
    requested_date = convert_date_format(today_date + timedelta(date_offset))
    call_target = call_args[1]
    user = users_dict.get(u_id)
    try:
        if call_target == "schedule":
            new_schedule = user.schedule.get_by_date(date_offset)
            text = parse_schedule(new_schedule)
        elif call_target == "marks":
            marks = user.marks.get_by_date(date_offset)
            text = parse_marks(marks)
        elif call_target == "homework":
            hw = user.homework.get_by_date(date_offset)
            text = parse_homework(hw)

    except (RequestError, NullFieldError):
        text = "На указанную дату ничего не найдено!"
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"{requested_date}\n{text}", reply_markup=call.message.reply_markup)

@bot.callback_query_handler(lambda call: call.data.startswith("TRIMESTER"))
def trimester_callback_handler(call):
    trimester_id = int(call.data[-1])
    user = users_dict.get(call.from_user.id)
    raw_trimester_data = user.marks.get_per_trimester(trimester_id - 1)
    if raw_trimester_data is None:
        text = f"У вас нет оценок за аттестационный период {trimester_id}!"
    else:
        text = f"Аттестационный период {trimester_id}\n\n{parse_trimester(raw_trimester_data)}"
    try:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, reply_markup=call.message.reply_markup)
    except ApiTelegramException:
        return

@bot.message_handler(content_types=["text"])
def text_handler(message):
    bot.send_message(message.chat.id, "Неизвестная команда!")

if __name__ == "__main__":
    bot.infinity_polling()

