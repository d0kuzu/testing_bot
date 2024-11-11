import sqlite3

import pytz
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
import calendar
import datetime
import config
import methods
from config import months, con
from typing import Optional
from aiogram.filters.callback_data import CallbackData
from factories import *
from methods import *


# con = sqlite3.connect("database.db", timeout=30)
# cursor = con.cursor(buffered=True)


def main_actions(user_id, username, add_remove_exam=False) -> ReplyKeyboardMarkup:
    con.reconnect()
    cursor = con.cursor(buffered=True)
    cursor.execute(f"select test_status from users_data where user_id={user_id}")
    status = cursor.fetchone()
    keyboard = [
        [KeyboardButton(text="Главная"), KeyboardButton(text="Подробная информация"), KeyboardButton(text="Контакты")],
        [KeyboardButton(text="Записаться на тестирование")]
    ]
    # keyboard[1].append(KeyboardButton(text="Проверить подпись договора"))
    if add_remove_exam and methods.get_test_status(user_id, username) == 1:
        keyboard[1].append(KeyboardButton(text="Отменить тестирование"))
    if methods.get_test_status(user_id, username) not in [1, None]:
        keyboard[1].pop(0)
    # if methods.get_test_status(user_id, username) in [2, 3]:
    #     keyboard.append([KeyboardButton(text="Завершить тестирование")])
    if config.DEV_MODE:
        keyboard.append([KeyboardButton(text="Подписать договор")])
        keyboard.append([KeyboardButton(text="/start"), KeyboardButton(text="/remake")])
    # if user_id == config.checker_id:
    #     keyboard.append([KeyboardButton(text="Изменить тексты")])
    kb = ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=keyboard
    )
    return kb


def get_calendar(year, month, message) -> InlineKeyboardMarkup:
    con.reconnect()
    try:
        caldr = calendar.monthcalendar(year, month)
        today = datetime.datetime.now(tz=pytz.FixedOffset(300))
        # today = datetime.datetime(day=30, month=3, year=2024)
        open_days = today + datetime.timedelta(days=7)
        header = [InlineKeyboardButton(text="❌", callback_data="nothing"),
                  f"{months[month]} {year}",
                  InlineKeyboardButton(text="❌", callback_data="nothing")]
        monthLink = 0
        if open_days.month != today.month and today.year == open_days.year:
            logging.info(f"{open_days.month} < {month}")
            if open_days.month < month:
                header[0] = InlineKeyboardButton(text=months[month - 1],
                                                 callback_data=DateCallbackFactory(action="month",
                                                                                   day=1,
                                                                                   year=year,
                                                                                   month=month - 1).pack())
                monthLink = month - 1
            elif open_days.month > month:
                header[2] = InlineKeyboardButton(text=months[month + 1],
                                                 callback_data=DateCallbackFactory(action="month",
                                                                                   day=1,
                                                                                   year=year,
                                                                                   month=month + 1).pack())
            elif open_days.month > today.month:
                header[0] = InlineKeyboardButton(text=months[month - 1],
                                                 callback_data=DateCallbackFactory(action="month",
                                                                                   day=1,
                                                                                   year=year,
                                                                                   month=month - 1).pack())
        calendar_buttons = []
        for row in range(len(caldr)):
            calendar_buttons.append([])
            for column in range(len(caldr[row])):
                date_num = caldr[row][column]
                if date_num == 0:
                    date_num = " "
                elif not (today.timetuple().tm_yday <= datetime.datetime(year, month, date_num).timetuple().tm_yday <
                          today.timetuple().tm_yday + 7) or (date_num == today.day and today.hour == 23):
                    date_num = "❌"
                if date_num == " " or date_num == "❌":
                    calendar_buttons[row].append(InlineKeyboardButton(text=str(date_num), callback_data="nothing"))
                else:
                    calendar_buttons[row].append(InlineKeyboardButton(
                        text=str(date_num),
                        callback_data=DateCallbackFactory(action="set_date", day=date_num,
                                                          month=month, year=year).pack()))

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                                [header[0],
                                 InlineKeyboardButton(text=header[1], callback_data="nothing"),
                                 header[2]]
                            ] + calendar_buttons
        )
        cursor = con.cursor(buffered=True)
        cursor.execute(f"SELECT date FROM users_data WHERE user_id = {message.from_user.id}")
        row = cursor.fetchall()
        cursor.close()
        if row != [] and row[0][0] is not None:
            datetime_object = datetime.datetime.strptime(row[0][0], '%Y-%m-%d %H:%M:%S')
            kb = galochka_date_db(return_keyboard=kb, db_day=datetime_object.day,
                                  db_month=datetime_object.month,
                                  db_year=datetime_object.year)
        return kb
    except Exception:
        logging.error("Error on get_calendar()")


def get_times(callback) -> InlineKeyboardMarkup:
    con.reconnect()
    times = []
    start_time = 0
    cursor = con.cursor(buffered=True)
    cursor.execute(f"SELECT date FROM users_data WHERE user_id={callback.from_user.id}")
    select = cursor.fetchall()[0][0]
    cursor.close()
    db_day = datetime.datetime.strptime(select, '%Y-%m-%d %H:%M:%S')
    today = datetime.datetime.now(tz=pytz.FixedOffset(300))
    if today.year == db_day.year and today.month == db_day.month and today.day == db_day.day:
        start_time = (today + datetime.timedelta(hours=1)).hour
    for hour in range(start_time, 24):
        times.append(InlineKeyboardButton(text=f"{hour}:00",
                                          callback_data=TimeCallbackFactory(
                                              action="times",
                                              hour=hour,
                                              minute=0).pack()))
    true_times = []
    for i in range(len(times) // 3 + 1):
        true_times.append([])
        for j in range(3):
            if len(times) != 0:
                true_times[i].append(times[0])
                times.pop(0)
    true_times += [[InlineKeyboardButton(text=f"Назад  ◀️", callback_data="back_to_date")]]
    return_keyboard = InlineKeyboardMarkup(inline_keyboard=true_times)
    galochka_time_db(return_keyboard, callback)
    return return_keyboard


def keyboard_is_exam_complete(from_who, sender) -> InlineKeyboardMarkup:
    con.reconnect()
    if from_who == 0:
        texts = ["Отправить тестирование", "Не отправлять"]
    if from_who == 1:
        texts = ["Принять тестирование", "Отклонить тестирование"]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=texts[0], callback_data=IsCompleteCallbackFactory(action="isComplete",
                                                                                     is_complete=1,
                                                                                     from_who=from_who,
                                                                                     sender=sender).pack())],
        [InlineKeyboardButton(text=texts[1], callback_data=IsCompleteCallbackFactory(action="isComplete",
                                                                                     is_complete=0,
                                                                                     from_who=from_who,
                                                                                     sender=sender).pack())]
    ])
    return keyboard


on_task = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Приступить к тестированию",
                                                                      callback_data="on_task")]])


# Возвращает массив кнопок тэг-текстов
def edit_texts() -> InlineKeyboardMarkup:
    tags = sql_db_select(columns=["tag"], table="texts")
    builder = InlineKeyboardBuilder()
    for tag in tags:
        builder.add(InlineKeyboardButton(text=tag[0]))
    builder.adjust(3)
    return builder.as_markup()
