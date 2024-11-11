import asyncio
import datetime
import logging

import coloredlogs
import pytz
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import callback_router
import config
import keyboards
import routers
from config import TOKEN, con
from factories import IsCompleteCallbackFactory, TimeCallbackFactory
from methods import send_testing_message_callback

from NDAService.handlers import GenerateKeyboard
from NDAService.handlers import router as NDARouter
from aiogram.types import FSInputFile
from config import PATHS

bot = Bot(token=TOKEN)
dp = Dispatcher()
dp.include_routers(routers.router, callback_router.router, NDARouter)
coloredlogs.install()


# cursor = con.cursor(buffered=True)


@dp.callback_query(IsCompleteCallbackFactory.filter(F.action == "isComplete"))
async def times(callback: types.CallbackQuery, callback_data: IsCompleteCallbackFactory):
    con.reconnect()
    if callback_data.from_who == 0:
        if callback_data.is_complete == 0:
            await callback.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=[]))
        elif callback_data.is_complete == 1:
            await callback.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=[]))
            await send_testing_message_callback(callback, to_complete=True)
            for c_id in config.checker_ids:
                await callback.message.send_copy(c_id, reply_markup=keyboards.
                                                 keyboard_is_exam_complete(from_who=1, sender=callback.from_user.id))
            cursor = con.cursor(buffered=True)
            cursor.execute("UPDATE users_data SET test_status=%s WHERE user_id=%s", (4, callback.from_user.id))
            con.commit()
            cursor.close()
    elif callback_data.from_who == 1:
        if callback_data.is_complete == 0:
            await callback.message.answer(text=f"Вы отклонили тестирование @{callback.from_user.username} ❌")
            await callback.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=[]))
            await bot.send_message(callback_data.sender, text=f"Тестирование отклонено❌",
                                   reply_markup=keyboards.main_actions(callback.from_user.id,
                                                                       callback.from_user.username))
        elif callback_data.is_complete == 1:
            await callback.message.answer(text=f"Вы приняли тестирование @{callback.from_user.username} ✅")
            await callback.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=[]))
            await bot.send_message(callback_data.sender, text=f"✅ Тестирование принято", 
                                   reply_markup=InlineKeyboardMarkup(inline_keyboard=[]))
            await send_testing_message_callback(callback, to_complete=True)
            
            # dokuzunosaidostaato

            await bot.send_document(callback_data.sender, FSInputFile(f'{PATHS["data"]}nda.docx'))
            await bot.send_message(callback_data.sender, text='Ознакомьтесь с документом 🙂')
            await bot.send_message(callback_data.sender, text='Теперь вам надо отправить свои данные для подписания NDA \nВыберите метод отправки вашего удостверение личности',
                                   reply_markup=GenerateKeyboard({'Фотография': 'img', 'PDF файл': 'pdf'}))
    await callback.answer()


from aiogram.filters import Command

@dp.message(Command("suidjas123"))
async def Start(msg: types.Message):
    print('command asd')
    await msg.answer(text='ВЫберите метод отправки фотографии вашего удостверение личности', reply_markup=GenerateKeyboard({'Фотография': 'img', 'PDF файл': 'pdf'}))


@dp.callback_query(TimeCallbackFactory.filter(F.action == "times"))
async def times(callback: types.CallbackQuery, callback_data: TimeCallbackFactory):
    con.reconnect()
    return_keyboard = keyboards.get_times(callback)
    correct_time = f"{callback_data.hour}:{callback_data.minute}0"
    # correct_time = f"20:24"
    user_config = (correct_time, callback.from_user.id)
    cursor = con.cursor(buffered=True)
    cursor.execute("UPDATE users_data SET time=%s WHERE user_id=%s", user_config)
    con.commit()
    for row in range(len(callback.message.reply_markup.inline_keyboard)):
        for data in range(len(callback.message.reply_markup.inline_keyboard[row])):
            if callback.message.reply_markup.inline_keyboard[row][data].text == \
                    f"{callback_data.hour}:{callback_data.minute}0":
                cursor.execute("UPDATE users_data SET time=%s, test_status=1 WHERE user_id=%s",
                               (f"{callback_data.hour}:{callback_data.minute}0", callback.from_user.id))
                con.commit()
                cursor.execute(f"SELECT date, time FROM users_data WHERE user_id = {callback.from_user.id}")
                row_db = cursor.fetchall()
                if row_db != [] and row_db[0][0] is not None and row_db[0][1] is not None:
                    date_to = datetime.datetime.strptime(row_db[0][0].split(" ")[0] + " " + row_db[0][1],
                                                         '%Y-%m-%d %H:%M')
                else:
                    return callback.message.answer(text="Произошла ошибка")
                # if config.DEV_MODE:
                #     date_now = datetime.datetime.now(tz=pytz.FixedOffset(300))
                #     date_to = datetime.datetime(year=date_now.year, month=date_now.month, day=date_now.day,
                #                                 hour=date_now.hour, minute=date_now.minute)
                #     date_to += datetime.timedelta(minutes=1)
                #     timed = datetime.time(hour=date_to.hour, minute=date_to.minute).strftime("%H:%M")
                #     cursor.execute(f"update users_data set date=%s, time=%s"
                #                    f" where user_id={callback.from_user.id}",
                #                    (date_to, f"{timed}"))
                #     con.commit()
                scheduler = AsyncIOScheduler(timezone="Asia/Almaty")
                started_at = datetime.datetime.strptime(
                    datetime.datetime.now(tz=pytz.FixedOffset(300)).strftime("%Y-%m-%d %H:%M"), "%Y-%m-%d "
                                                                                                "%H:%M")
                cursor.execute("UPDATE users_data SET run_date=%s WHERE user_id=%s",
                               (started_at, callback.from_user.id))
                con.commit()
                scheduler.add_job(send_testing_message_callback, trigger='date', run_date=date_to,
                                  kwargs={"callback": callback, "run_date": started_at, "test_status": 2})
                scheduler.add_job(send_testing_message_callback, trigger='date',
                                  run_date=str(date_to + config.exam_times["send_notification"]),
                                  kwargs={"callback": callback, "run_date": started_at, "test_status": 3})
                scheduler.add_job(send_testing_message_callback, trigger='date',
                                  run_date=str(date_to + config.exam_times["duration"]),
                                  kwargs={"callback": callback, "run_date": started_at, "test_status": 5})
                scheduler.start()

                return_keyboard.inline_keyboard[row][data].text = "✅"
    try:
        await callback.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=[]))
        await callback.message.edit_text(text=f"Вы выбрали время: {callback_data.hour}:{callback_data.minute}0")
    except Exception:
        print("keyboard not modified")
    cursor.execute(f"SELECT date, time FROM users_data WHERE user_id = {callback.from_user.id}")
    row_db = cursor.fetchall()
    cursor.close()
    await callback.answer()
    dates = row_db[0][0].split(' ')[0].split('-')
    date = f"{dates[2]}.{dates[1]}.{dates[0]}"
    await callback.message.answer(text="Ура! Вы назначили себе задание! 🙂"
                                       "\n"
                                       f"\nДата: {date}"
                                       f"\nВремя: {row_db[0][1]}"
                                       "\nВремя на выполнение: 4 часа"
                                       "\n"
                                       "\nТеперь ожидайте задание 🙂",
                                  reply_markup=keyboards.main_actions(user_id=callback.from_user.id,
                                                                      username=callback.from_user.username,
                                                                      add_remove_exam=
                                                                      routers.exist_datetime(callback.from_user.id)))
    for c_id in config.checker_ids:
        await bot.send_message(chat_id=c_id, text=f"@{callback.from_user.username} {callback.from_user.full_name}"
                                                  f"\n"
                                                  f"записался на тестирование:"
                                                  f"\n"
                                                  f"\nДата: {date}"
                                                  f"\nВремя: {row_db[0][1]}")


@dp.callback_query(F.data == "on_task")
async def month(callback: types.CallbackQuery):
    con.reconnect()
    await callback.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=[]))
    for c_id in config.checker_ids:
        await bot.send_message(chat_id=c_id, text=f"@{callback.from_user.username} приступил к тестированию")
    await callback.message.edit_text(text="Вы начали тестирование ✅")
    today = datetime.datetime.now(tz=pytz.FixedOffset(300))
    cursor = con.cursor()
    cursor.execute("UPDATE users_data SET on_task=%s WHERE user_id=%s", (today, callback.from_user.id))
    con.commit()
    cursor.close()
    await callback.answer()


async def start_bot():
    con.reconnect()
    logging.basicConfig(level=logging.DEBUG)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(start_bot())
