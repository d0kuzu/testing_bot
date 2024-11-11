import datetime
import logging
import coloredlogs
import pytz
import tzlocal
from dateutil import tz
from aiogram import Router, F, types
import config
import keyboards
import methods
import routers
from config import con
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.types import InlineKeyboardMarkup
from factories import *
from methods import galochka_date_change, send_testing_message_callback

router = Router()
coloredlogs.install(level=logging.DEBUG)
# cursor = con.cursor(buffered=True)


@router.callback_query(DateCallbackFactory.filter(F.action == "set_date"))
async def send_random_value(callback: types.CallbackQuery, callback_data: DateCallbackFactory):
    con.reconnect()
    return_keyboard = callback.message.reply_markup
    cursor = con.cursor(buffered=True)
    cursor.execute(f"UPDATE users_data set test_status=1 where user_id={callback.from_user.id}")
    con.commit()
    cursor.close()
    return_keyboard = galochka_date_change(callback=callback, callback_data=callback_data,
                                           return_keyboard=return_keyboard)
    try:
        await callback.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=[]))
        today = datetime.datetime.now(tz=pytz.FixedOffset(300)).strftime("%d.%m.%Y")
        await callback.message.edit_text(text=f"Дата выполнения задания: {today}")
    except Exception:
        print("Клавиатура не изменена")
    await callback.message.answer(f"Выберите удобное время  🕗"
                                  f"\nИли напишите своё время", reply_markup=keyboards.get_times(callback))
    await callback.answer()


@router.callback_query(F.data == "nothing")
async def nothing(callback: types.CallbackQuery):
    await callback.answer()


@router.callback_query(DateCallbackFactory.filter(F.action == "month"))
async def month(callback: types.CallbackQuery, callback_data: DateCallbackFactory):
    try:
        await callback.message.edit_reply_markup(reply_markup=keyboards.get_calendar(year=callback_data.year,
                                                                                     month=callback_data.month,
                                                                                     message=callback))
    except Exception:
        logging.error("Month select error")
    await callback.answer()


@router.callback_query(F.data == "back_to_date")
async def month(callback: types.CallbackQuery):
    await callback.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=[]))
    await callback.message.edit_text(text="Вы вернулись назад  ◀️")
    today = datetime.datetime.now(tz=pytz.FixedOffset(300))
    await callback.message.answer(
        f"Выберите удобную дату  📅",
        reply_markup=keyboards.get_calendar(today.year, today.month, callback)
    )
    await callback.answer()


