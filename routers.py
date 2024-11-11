import datetime
import logging

import coloredlogs
import pytz
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

import config
import keyboards
import methods
from config import con
from methods import exist_datetime

from aiogram.fsm.context import FSMContext
from aiogram.types import InputMediaPhoto
from aiogram.types import FSInputFile

from NDAService.handlers import GetCheckKeyboard
from EdoParseService.modules import CheckStatus
from NDAService.module import ReadTextRequsites, SendToAdmin, GetMonoText
from NDAService.handlers import GenerateKeyboard

router = Router()
# con = sqlite3.connect("database.db", timeout=30)
# cursor = con.cursor(buffered=True)
coloredlogs.install()


@router.message(Command("start"))
async def start(message: Message):
    await message.answer(
        f"Приветствую @{message.from_user.username}🙂🤝🏼 "
        f"\nЯ бот компании Stratton.kz"
        f"\nПомогу тебе получить практическое задание 👇",
        reply_markup=keyboards.main_actions(user_id=message.from_user.id,
                                            username=message.from_user.username,
                                            add_remove_exam=exist_datetime(message.from_user.id))
    )


@router.message(F.text == "Главная")
async def start(message: Message):
    await message.answer(
        f"Приветствую @{message.from_user.username}🙂🤝🏼 "
        f"\nЯ бот компании Stratton.kz"
        f"\nПомогу тебе получить практическое задание 👇",
        reply_markup=keyboards.main_actions(user_id=message.from_user.id,
                                            username=message.from_user.username,
                                            add_remove_exam=exist_datetime(message.from_user.id))
    )


@router.message(F.text == "Подробная информация")
async def info(message: Message):
    await message.answer(f"""🏬  Компания Stratton.kz

🤖 Мы автоматизируем бизнес-процессы посредством роботизации, внедрения чат-ботов и функциональных сайтов.

ℹ️ Подробнее о компании <a href="https://stratton.taplink.ws/p/o-kompanii/">тут</a>""",
                         reply_markup=keyboards.main_actions(user_id=message.from_user.id,
                                                             username=message.from_user.username,
                                                             add_remove_exam=exist_datetime(message.from_user.id)),
                         parse_mode="HTML"
                         )


@router.message(F.text == "Контакты")
async def info(message: Message):
    await message.answer(
        f"Для связи с нами пишите ✍️"
        f"\n@alfinkly",
        reply_markup=keyboards.main_actions(user_id=message.from_user.id,
                                            username=message.from_user.username,
                                            add_remove_exam=exist_datetime(message.from_user.id))
    )


@router.message(F.text == "Записаться на тестирование")
async def info(message: Message):
    if methods.get_test_status(message.from_user.id, message.from_user.username) in [1, None]:
        today = datetime.datetime.now(tz=pytz.FixedOffset(300))
        await message.answer(
            f"Выберите удобную дату: 📅",
            reply_markup=keyboards.get_calendar(today.year, today.month, message)
        )
    elif methods.get_test_status(message.from_user.id, message.from_user.username) in [2, 3, 4]:
        await message.answer("Нельзя перезаписать начавшееся тестирование. ❌")
    elif methods.get_test_status(message.from_user.id, message.from_user.username) in [5, 6]:
        await message.answer(
            f"Тестирование было пройдено."
            f"\n"
            f"\nПо вопросам пересдачи пишите ✍️"
            f"\n@alfinkly"
        )


@router.message(F.text == "Юху")
async def info(message: Message):
    await message.answer(
        f"Юхууу",
        reply_markup=keyboards.main_actions(user_id=message.from_user.id,
                                            username=message.from_user.username,
                                            add_remove_exam=exist_datetime(message.from_user.id))
    )


# @router.message(F.text == "Проверить подпись договора")
# async def info(message: Message, state: FSMContext):
#     data = await state.get_data()
#     print(data)
#     print(methods.get_test_status(message.from_user.id, message.from_user.username))
#     if data.get('data') and methods.get_test_status(message.from_user.id, message.from_user.username) == 4:
#         status = CheckStatus(data['data'])
#         await message.answer(f'Статус договора: {status}')
#     else:
#         await message.answer('Закончите отправку данных удостоверения, и дождитесь окончание проверки данных')


@router.message(F.text == "Подписать договор")
async def Doc(message: Message):
    await message.answer(f'От какого лица вы будете подписать договор', reply_markup=GenerateKeyboard({'Юридическое лицо': 'ur', 'Физическое лицо': 'fiz'}))


@router.message(F.text == "Отменить тестирование")
async def add_remove_exam(message: Message):
    try:
        if methods.get_test_status(message.from_user.id, message.from_user.username) == 1:
            cursor = con.cursor(buffered=True)
            cursor.execute(f"UPDATE users_data SET date=NULL, time=NULL, test_status=NULL "
                           f"WHERE user_id={message.from_user.id}")
            con.commit()
            cursor.close()
            return await message.answer(text="Ваше тестирование удалено. ❌",
                                        reply_markup=keyboards.main_actions(user_id=message.from_user.id,
                                                                            username=message.from_user.username,
                                                                            add_remove_exam=exist_datetime(
                                                                                message.from_user.id)))
        elif methods.get_test_status(message.from_user.id, message.from_user.username) in [2, 3, 4]:
            return await message.answer(text="Нельзя отменить начавшееся тестирование. ❌",
                                        reply_markup=keyboards.main_actions(user_id=message.from_user.id,
                                                                            username=message.from_user.username,
                                                                            add_remove_exam=exist_datetime(
                                                                                message.from_user.id)))
        elif methods.get_test_status(message.from_user.id, message.from_user.username) in [5, 6]:
            return await message.answer(text="Нельзя отменить пройденное тестирование. ❌",
                                        reply_markup=keyboards.main_actions(user_id=message.from_user.id,
                                                                            username=message.from_user.username,
                                                                            add_remove_exam=exist_datetime(
                                                                                message.from_user.id)))
    except Exception:
        return await message.answer(text="Не удалось удалить тестирование.",
                                    reply_markup=keyboards.main_actions(user_id=message.from_user.id,
                                                                        username=message.from_user.username,
                                                                        add_remove_exam=exist_datetime(
                                                                            message.from_user.id)))


@router.message(Command("remake"))
async def start(message: Message):
    try:
        if config.DEV_MODE:
            cursor = con.cursor(buffered=True)
            cursor.execute(f"DELETE FROM users_data")
            con.commit()
            cursor.close()
            logging.info("DB remaked")
            await message.answer(text="АНИГИЛЯЦИЯ УСПЕШНА",
                                 reply_markup=keyboards.main_actions(user_id=message.from_user.id,
                                                                     username=message.from_user.username,
                                                                     add_remove_exam=exist_datetime(
                                                                         message.from_user.id)))
    except Exception:
        logging.error("Remake error")


@router.message(F.video)
async def video(message: Message):
    if methods.get_test_status(message.from_user.id, message.from_user.username) in [2, 3]:
        cursor = con.cursor(buffered=True)
        cursor.execute(f"SELECT date, time FROM users_data WHERE user_id = {message.from_user.id}")
        row_db = cursor.fetchall()
        date_to = datetime.datetime.strptime(row_db[0][0].split(" ")[0] + " " + row_db[0][1], '%Y-%m-%d %H:%M')
        date_to = pytz.timezone('Asia/Almaty').localize(date_to)
        now = datetime.datetime.now(tz=pytz.timezone('Asia/Almaty'))
        video_format = message.video.mime_type.lower()
        if message.video.duration > 60:
            return await message.reply("Извините, видео должно быть не более 60 секунд. 🕗")
        if message.video.file_size > 10485760:  # 10 МБ в байтах
            return await message.reply("Извините, видео должно весить не более 10МБ. 💾")
        if not (video_format in ["video/mp4", "video/quicktime"]):
            return await message.reply(
                "Извините, формат видео недопустим. Только видео с расширением .mov или .mp4 ")
        if date_to < now < date_to + config.exam_times["duration"]:
            cursor.execute(f"SELECT tasks FROM users_data WHERE user_id={message.from_user.id}")
            tasks_text = cursor.fetchone()
            await message.answer_video(video=message.video.file_id,
                                       reply_markup=keyboards.keyboard_is_exam_complete(from_who=0,
                                                                                        sender=message.from_user.id),
                                       caption=f"Тестирование @{message.from_user.username}"
                                               f"\n\nЗадание: \n"
                                               f"{tasks_text[0]}\n\n"
                                       )
            con.commit()
            cursor.close()
    elif methods.get_test_status(message.from_user.id, message.from_user.username) in [5, 6]:
        await message.answer("Вы отправили видео не в срок! ⌛️")
    elif methods.get_test_status(message.from_user.id, message.from_user.username) == 4:
        await message.answer("Вы уже отправили тестирование! ❌")


@router.message(F.text)
async def format_time(message: Message, state: FSMContext):
    data = await state.get_data()
    
    if data.get('textRequisites'):
        fields = ReadTextRequsites(message.text)
        if len(fields)!=0:
            await state.clear()
            await state.update_data(fields)
            await SendToAdmin(message, 
                                state, 
                                GenerateKeyboard({'Изменить':'change', 'Всё верно':'allright'}),
                                requisites=message.text,
                                document='документа') 
        else:
            await message.answer('Это не похоже на реквизиты')

    if data.get('change'):
        fields = []
        text = data['text'].split('\n')
        for i in range(len(text)):
            asd = text[i].split('\-')
            if len(asd)==2:
                fields.append(asd[0])
            if asd[0]==data['change']:
                text[i] = f"{asd[0]}\-`{GetMonoText(message.text)}`"
        text='\n'.join(text)
        await state.update_data(text=text)
    
        if data.get('fImageId'):
            media = []
            photoPaths = [data['fImageId'], data['sImageId']]
            for path in photoPaths:
                media.append(InputMediaPhoto(media=path))
            await message.answer_media_group(media=media)
        elif data.get('fileName'):
            await message.answer_document(FSInputFile(data['fileName']))
        else:
            await message.answer(data['requisites'])
        await message.answer(text, reply_markup=GetCheckKeyboard(fields), parse_mode='MarkdownV2')

    # dokuzunosaiduowari

    cursor = con.cursor(buffered=True)
    cursor.execute(f"select test_status from users_data where user_id={message.from_user.id}")
    if methods.get_test_status(message.from_user.id, message.from_user.username) == 1:
        is_time = False
        for time_format in ["%H:%M", "%H %M", "%H-%M", "%H.%M", "%H_%M"]:
            try:
                time = datetime.datetime.strptime(message.text, time_format)
                is_time = True
                await methods.appoint_test(message, time)
                break
            except ValueError:
                pass
        if not is_time:
            await message.answer("Это не похоже на время")
    elif methods.get_test_status(message.from_user.id, message.from_user.username) in [2, 3]:
        if (message.text.startswith("@") and message.text.endswith("bot") and not (" " in message.text)) or \
                (message.text.startswith("https://t.me/") and message.text.endswith("bot") and
                 not (" " in message.text)):
            cursor.execute(f"SELECT date, time FROM users_data WHERE user_id = {message.from_user.id}")
            row_db = cursor.fetchall()
            date_to = datetime.datetime.strptime(row_db[0][0].split(" ")[0] + " " + row_db[0][1], '%Y-%m-%d %H:%M')
            now = datetime.datetime.now(tz=pytz.FixedOffset(300))
            if date_to < now < date_to + config.exam_times["duration"]:  # or config.DEV_MODE:
                await message.send_copy(message.from_user.id,
                                        reply_markup=keyboards.keyboard_is_exam_complete(from_who=0,
                                                                                         sender=message.from_user.id))
        else:
            await message.reply("Это не похоже на ссылку на бота.")
    elif methods.get_test_status(message.from_user.id, message.from_user.username) == 4:
        await message.answer("Вы уже отправили тестирование! ❌")
    cursor.close()
