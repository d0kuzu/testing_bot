import calendar
import datetime
import logging
import random

import coloredlogs
import pytz
from aiogram.types import CallbackQuery, Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import config
import keyboards
from config import con

coloredlogs.install()


def galochka_date_change(callback, callback_data, return_keyboard):
    con.reconnect()
    cursor = con.cursor(buffered=True)
    return_keyboard = return_keyboard
    caldr = calendar.monthcalendar(callback_data.year, callback_data.month)
    for row in range(len(callback.message.reply_markup.inline_keyboard)):
        for data in range(len(callback.message.reply_markup.inline_keyboard[row])):
            if callback.message.reply_markup.inline_keyboard[row][data].text == "✅":
                return_keyboard.inline_keyboard[row][data].text = str(caldr[row - 1][data])
            if callback.message.reply_markup.inline_keyboard[row][data].text == str(callback_data.day):
                user_config = (datetime.datetime(year=callback_data.year,
                                                 month=callback_data.month,
                                                 day=callback_data.day),
                               callback.from_user.id)
                cursor.execute("UPDATE users_data SET date=%s WHERE user_id=%s", user_config)
                con.commit()
                cursor.close()
                return_keyboard.inline_keyboard[row][data].text = "✅"
    return return_keyboard


def galochka_date_db(return_keyboard, db_day, db_month, db_year):
    con.reconnect()
    return_keyboard = return_keyboard
    # caldr = calendar.monthcalendar(db_year, db_month)
    for row in range(len(return_keyboard.inline_keyboard)):
        for data in range(len(return_keyboard.inline_keyboard[row])):
            if return_keyboard.inline_keyboard[row][data].text == str(db_day) and \
                    return_keyboard.inline_keyboard[row][data].callback_data.split(":")[-1] == str(db_year) and \
                    return_keyboard.inline_keyboard[row][data].callback_data.split(":")[-2] == str(db_month):
                return_keyboard.inline_keyboard[row][data].text = "✅"
    return return_keyboard


def galochka_time_change(callback, callback_data, return_keyboard, time):
    con.reconnect()
    for row in range(len(callback.message.reply_markup.inline_keyboard)):
        for data in range(len(callback.message.reply_markup.inline_keyboard[row])):
            if callback.message.reply_markup.inline_keyboard[row][data].text == "✅":
                time = f"{return_keyboard.inline_keyboard[row][data].callback_data.split(':')[-2]}:" \
                       f"{return_keyboard.inline_keyboard[row][data].callback_data.split(':')[-1]}0"
                return_keyboard.inline_keyboard[row][data].text = time

            if callback.message.reply_markup.inline_keyboard[row][data].text == time:
                # if callback.message.reply_markup.inline_keyboard[row][data].text ==\
                #     f"{callback_data.hour}:{callback_data.minute}0":
                user_config = (f"{callback_data.hour}:{callback_data.minute}0", callback.from_user.id)
                cursor = con.cursor(buffered=True)
                cursor.execute("UPDATE users_data SET time=%s WHERE user_id=%s", user_config)
                con.commit()
                cursor.close()
                return_keyboard.inline_keyboard[row][data].text = "✅"
    return return_keyboard


def galochka_time_db(return_keyboard, callback):
    con.reconnect()
    cursor = con.cursor(buffered=True)
    cursor.execute(f"SELECT time FROM users_data WHERE user_id={callback.from_user.id}")
    db_row = cursor.fetchall()
    cursor.close()
    if db_row[0][0] is not None:
        time = db_row[0][0]
    else:
        return return_keyboard
    for row in range(len(return_keyboard.inline_keyboard)):
        for data in range(len(return_keyboard.inline_keyboard[row])):
            if return_keyboard.inline_keyboard[row][data].text == "✅":
                time = f"{return_keyboard.inline_keyboard[row][data].callback_data.split(':')[-2]}:" \
                       f"{return_keyboard.inline_keyboard[row][data].callback_data.split(':')[-1]}0"
                return_keyboard.inline_keyboard[row][data].text = time
            if return_keyboard.inline_keyboard[row][data].text == time:
                # user_config = (f"{callback_data.hour}:{callback_data.minute}0", callback.from_user.id)
                # cursor.execute("UPDATE users_data SET time=%s WHERE user_id=%s", user_config)
                # con.commit()
                return_keyboard.inline_keyboard[row][data].text = "✅"
    return return_keyboard


def exist_datetime(user_id) -> bool:
    con.reconnect()
    cursor = con.cursor(buffered=True)
    cursor.execute(f"SELECT date, time FROM users_data WHERE user_id = {user_id}")
    row = cursor.fetchall()
    cursor.close()
    try:
        if row[0][0] is not None and row[0][1] is not None:
            return True
    except Exception:
        logging.warning("Нет даты и времени в базе данных")
    return False


# Функция для получения данных пользователя из базы данных
def get_user_data(user_id):
    con.reconnect()
    cursor = con.cursor(buffered=True)
    cursor.execute(f"SELECT test_status, run_date FROM users_data WHERE user_id = {user_id}")
    data = cursor.fetchone()
    cursor.close()
    return data


# Функция для обновления статуса тестирования пользователя в базе данных
def update_test_status(user_id, status):
    con.reconnect()
    cursor = con.cursor(buffered=True)
    cursor.execute("UPDATE users_data SET test_status=%s WHERE user_id=%s", (status, user_id))
    con.commit()
    cursor.close()


# Функция для проверки и обновления статуса тестирования
def check_and_update_test_status(user_id, current_status, new_status):
    if current_status == new_status - 1 or (current_status in [2, 3] and new_status in [4, 5]):
        update_test_status(user_id, new_status)
        return True
    return False


# Функция для начала тестирования
async def start_testing(message, user_id):
    ids = random.sample(range(len(config.tasks)), 3)
    tasks_text = "\n".join([f'{i + 1}) ' + config.tasks[ids[i]] for i in range(len(ids))])

    con.reconnect()
    cursor = con.cursor(buffered=True)
    cursor.execute("UPDATE users_data SET tasks=%s WHERE user_id=%s", (tasks_text, user_id))
    con.commit()
    cursor.close()
    if type(message) == Message:
        await message.answer(
            text="Ваше тестирование началось, успехов!\n\n"
                 "Время на выполнение: 4 часа\n"
                 "Задание будет на проверке когда вы отправите видео или ссылку "
                 "и нажмете кнопку \"Отправить тестирование\" ✅\n"
                 "Писать ботов только на aiogram 3 версии\n\n"
                 f"Задание: \n"
                 f"{tasks_text}\n\n"
                 "Результат выслать в формате:\n"
                 "- видео работы кода до 60 секунд и размером не более 10МБ\n",
            reply_markup=keyboards.main_actions(user_id=user_id, username=message.from_user.username)
        )
        await message.answer(
            text="Нажмите на кнопку когда приступите к тестированию",
            reply_markup=keyboards.on_task
        )
    elif type(message) == CallbackQuery:
        await message.message.answer(
            text="Ваше тестирование началось, успехов!\n\n"
                 "Время на выполнение: 4 часа\n"
                 "Задание будет на проверке когда вы отправите видео или ссылку "
                 "и нажмете кнопку \"Отправить тестирование\" ✅\n"
                 "Писать ботов только на aiogram 3 версии\n\n"
                 f"Задание: \n"
                 f"{tasks_text}\n\n"
                 "Результат выслать в формате:\n"
                 "- видео работы кода до 60 секунд и размером не более 10МБ\n",
            reply_markup=keyboards.main_actions(user_id=user_id, username=message.from_user.username)
        )
        await message.message.answer(
            text="Нажмите на кнопку когда приступите к тестированию",
            reply_markup=keyboards.on_task
        )


# Функция для отправки уведомлений администраторам
async def notify_admins(bot, username):
    for admin in config.checker_ids:
        await bot.send_message(admin, text=f"@{username} не прошел тестирование ❌")


# Основная функция для обработки тестирования
async def process_testing(user_id, message=None, to_complete=False, run_date=None, test_status=None):
    user_data = get_user_data(user_id)
    if user_data is None:
        return

    test_status_db, run_date_db = user_data
    if run_date_db is not None:
        run_date_db = datetime.datetime.strptime(run_date_db, "%Y-%m-%d %H:%M:%S")
        if run_date and run_date < run_date_db:
            return

    if to_complete:
        update_test_status(user_id, 6)
        return

    if test_status is not None:
        if not check_and_update_test_status(user_id, test_status_db, test_status):
            return

    if test_status == 2:
        await start_testing(message, user_id)
    elif test_status == 3:
        if type(message) == Message:
            await message.answer(
                text="У Вас есть 10 минут, чтобы отправить результаты!",
                reply_markup=keyboards.main_actions(user_id=user_id, username=message.from_user.username)
            )
        elif type(message) == CallbackQuery:
            await message.message.answer(
                text="У Вас есть 10 минут, чтобы отправить результаты!",
                reply_markup=keyboards.main_actions(user_id=user_id, username=message.from_user.username)
            )
    elif test_status == 5 and test_status_db in [2, 3]:
        if type(message) == Message:
            await message.answer(
                text="Ваше тестирование не выполнено\nПо вопросам пересдачи пишите ✍️\n@alfinkly",
                reply_markup=keyboards.main_actions(user_id=user_id, username=message.from_user.username)
            )
        elif type(message) == CallbackQuery:
            await message.message.answer(
                text="Ваше тестирование не выполнено\nПо вопросам пересдачи пишите ✍️\n@alfinkly",
                reply_markup=keyboards.main_actions(user_id=user_id, username=message.from_user.username)
            )
        await notify_admins(message.bot, message.from_user.username)


# Функция для обработки callback
async def send_testing_message_callback(callback: CallbackQuery, to_complete=False, run_date=None, test_status=None):
    await process_testing(callback.from_user.id, message=callback, to_complete=to_complete, run_date=run_date,
                          test_status=test_status)
    await callback.answer()


# Функция для обработки message
async def send_testing_message_m(message: Message, to_complete=False, run_date=None, test_status=None):
    await process_testing(message.from_user.id, message=message, to_complete=to_complete, run_date=run_date,
                          test_status=test_status)


def get_test_status(user_id, username):
    con.reconnect()
    cursor = con.cursor(buffered=True)
    cursor.execute(f"SELECT test_status, user_id FROM users_data WHERE user_id = {user_id}")
    row = cursor.fetchone()
    cursor.close()
    if row is None:
        add_user(user_id, username)
        return row
    return row[0]


def add_user(user_id, username):
    con.reconnect()
    cursor = con.cursor(buffered=True)
    cursor.execute(f"INSERT INTO users_data (user_id, username) VALUES (%s, %s);", (user_id, username))
    con.commit()
    cursor.close()
    logging.info(f"Пользователь @{username} с id - {user_id} добавлен")


async def appoint_test(message, time):
    con.reconnect()
    now = datetime.datetime.now(tz=pytz.FixedOffset(300))
    if time.hour <= now.hour and time.minute <= now.minute:
        return await message.answer(text="Указанное время уже прошло ⌛️. ")
    cursor = con.cursor(buffered=True)
    cursor.execute(
        f"UPDATE users_data SET time='{time.strftime('%H:%M')}', test_status=1 WHERE user_id={message.from_user.id}")
    con.commit()
    cursor.execute(f"SELECT date, time FROM users_data WHERE user_id = {message.from_user.id}")
    row_db = cursor.fetchone()
    if row_db != [] and row_db[0][0] is not None and row_db[0][1] is not None:
        date_to = datetime.datetime.strptime(row_db[0].split(" ")[0] + " " + time.strftime('%H:%M'),
                                             '%Y-%m-%d %H:%M')

    scheduler = AsyncIOScheduler(timezone="Asia/Almaty")
    started_at = datetime.datetime.strptime(
        datetime.datetime.now(tz=pytz.FixedOffset(300)).strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")
    cursor.execute("UPDATE users_data SET run_date=%s WHERE user_id=%s", (started_at, message.from_user.id))
    con.commit()
    scheduler.add_job(send_testing_message_m, trigger='date', run_date=date_to,
                      kwargs={"message": message, "run_date": started_at, "test_status": 2})
    scheduler.add_job(send_testing_message_m, trigger='date',
                      run_date=str(date_to + config.exam_times["send_notification"]),
                      kwargs={"message": message, "run_date": started_at, "test_status": 3})
    scheduler.add_job(send_testing_message_m, trigger='date', run_date=str(date_to +
                                                                           config.exam_times["duration"]),
                      kwargs={"message": message, "run_date": started_at, "test_status": 5})
    scheduler.start()
    cursor.execute(f"SELECT date, time FROM users_data WHERE user_id = {message.from_user.id}")
    row_db = cursor.fetchall()
    cursor.close()
    dates = row_db[0][0].split(' ')[0].split('-')
    date = f"{dates[2]}.{dates[1]}.{dates[0]}"
    await message.answer(text="Ура! Вы назначили себе задание! 🙂"
                              "\n"
                              f"\nДата: {date}"
                              f"\nВремя: {row_db[0][1]}"
                              "\nВремя на выполнение: 4 часа"
                              "\n"
                              "\nТеперь ожидайте задание 🙂",
                         reply_markup=keyboards.main_actions(user_id=message.from_user.id,
                                                             username=message.from_user.username,
                                                             add_remove_exam=exist_datetime(message.from_user.id)))
    for c_id in config.checker_ids:
        await message.bot.send_message(chat_id=c_id, text=f"@{message.from_user.username} {message.from_user.full_name}"
                                                          f"\nзаписался на тестирование:"
                                                          f"\n"
                                                          f"\nДата: {date}"
                                                          f"\nВремя: {row_db[0][1]}")


def sql_db_select(columns: list, filter=None, table="users_data"):
    con.reconnect()
    columns = ", ".join(columns)
    cursor = con.cursor()
    if filter is not None:
        query = f"SELECT {columns} FROM {table} WHERE {filter[0]}={filter[filter[0]]}"
        cursor.execute(query)
        row = cursor.fetchone()
    else:
        query = f"SELECT {columns} FROM {table}"
        cursor.execute(query)
        row = cursor.fetchall()
    cursor.close()
    logging.info(query)
    return row


def sql_db_update(columns: dict, filter: dict, table="users_date"):
    con.reconnect()
    set_query = ""

    for col in columns:
        set_query += col + "=" + str(columns[col]) + ", "
    else:
        set_query = set_query.removesuffix(", ")

    cursor = con.cursor()
    query = f"UPDATE {table} SET {set_query} WHERE {filter}={filter[filter[0]]}"
    cursor.execute(query)
    con.commit()
    cursor.close()

    logging.info(query)


def exist_user(user_id):
    con.reconnect()
    cursor = con.cursor()
    cursor.execute(f"SELECT user_id FROM users_data WHERE user_id={user_id}")
    if cursor.fetchone()[0] is not None:
        return True
    else:
        return False
