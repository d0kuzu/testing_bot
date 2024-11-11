from aiogram import Router, types, F
from aiogram.types import ContentType
from aiogram.fsm.context import FSMContext
from aiogram.filters.command import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from NDAService.callbacks import Callback, ChangeCallback, EdoCallback
from aiogram.filters.callback_data import CallbackQuery
from aiogram.types import FSInputFile
from aiogram.types import InputMediaPhoto
from NDAService.module import *
from config import PATHS, checker_ids
from EdoParseService.modules import Main
from keyboards import main_actions

router = Router()


def GenerateKeyboard(values):
    buttons=[]
    for i in values:
        buttons.append(InlineKeyboardButton(text=i, callback_data=Callback(action=values[i]).pack()))
    keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
    return keyboard


def GetCheckKeyboard(fields):
    buttons=[]
    for i in fields:
        buttons.append([InlineKeyboardButton(text=i, callback_data=ChangeCallback(action='changeField', field=i).pack())])
    buttons.append([InlineKeyboardButton(text='Все верно', callback_data=Callback(action='allright').pack())])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


# @router.message(Command("start"))
# async def Start(msg: types.Message):
#     await msg.answer(text='ВЫберите метод отправки фотографии вашего удостверение личности', reply_markup=GenerateKeyboard({'Фотография': 'img', 'PDF файл': 'pdf'}))


@router.callback_query(Callback.filter(F.action=='ur'))
async def LegalFace(cb: CallbackQuery):
    await cb.message.edit_text(text='Теперь вам надо отправить свои данные для подписания документа \nВыберите метод отправки реквизитов',
                          reply_markup=GenerateKeyboard({'Тект/сообщение': 'text', 'doc/docx файл': 'docx'}))


@router.callback_query(Callback.filter(F.action=='fiz'))
async def PhysicalFace(cb: CallbackQuery):
    await cb.message.edit_text(text='Теперь вам надо отправить свои данные для подписания NDA \nВыберите метод отправки вашего удостверение личности',
                          reply_markup=GenerateKeyboard({'Фотография': 'img', 'PDF файл': 'pdf'}))


@router.callback_query(Callback.filter(F.action=='text'))
async def TextRequisites(cb: CallbackQuery, state: FSMContext):
    await state.update_data(textRequisites=True)
    await cb.message.edit_text(text='Ожидание текста',
                          reply_markup=None)
    

@router.callback_query(Callback.filter(F.action=='docx'))
async def DocRequisites(cb: CallbackQuery, state: FSMContext):
    await state.update_data(docRequisites=True)
    await cb.message.edit_text(text='Ожидание файла',
                          reply_markup=None)


@router.callback_query(Callback.filter(F.action=='img'))
async def IMGHandler(cb: CallbackQuery, state: FSMContext):
    await state.update_data(face=True)
    await cb.message.edit_text(text='Отправьте фотографию лицевой стороны удостверения личности \nЕсли у вас не получается отсканировать данные, пропустите этап нажав на кнопку "пропустить" 🙂')
    

@router.callback_query(Callback.filter(F.action=='pdf'))
async def IMGHandler(cb: CallbackQuery, state: FSMContext):
    await state.update_data(pdf=True)
    await cb.message.edit_text(text='Отправьте PDF файл вашего удостоверения личности')


@router.message(F.content_type == ContentType.DOCUMENT)
async def process_document(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    if data.get('pdf'):
        file_name = f"{PATHS['data']}{msg.from_user.id}.pdf"
        await msg.bot.download(msg.document, destination=file_name)
        fields = ReadPDF(file_name)
        if fields and len(fields)!=0:
            await state.clear()
            asd = fields|dict((k, v) for k,v in data.items() if k != 'pdf')
            await state.update_data(asd)

            await SendToAdmin(msg, 
                                state, 
                                GenerateKeyboard({'Изменить':'change', 'Всё верно':'allright'}),
                                file_name,
                                document='NDA') 
        elif len(fields)==0:
            await msg.answer('Этот файл не похож на удостоверение личности')
        else:
            await msg.answer('Произошла ошибка, повторите попытку')
    elif data.get('docRequisites'):
        file_name = f"{PATHS['data']}{msg.from_user.id}.docx"
        await msg.bot.download(msg.document, destination=file_name)
        fields = ReadDOCX(file_name)
        if fields and len(fields)!=0:
            await state.clear()
            asd = fields|dict((k, v) for k,v in data.items() if k != 'pdf')
            await state.update_data(asd)

            await SendToAdmin(msg, 
                                state, 
                                GenerateKeyboard({'Изменить':'change', 'Всё верно':'allright'}),
                                file_name,
                                document='NDA') 
        elif len(fields)==0:
            await msg.answer('Этот файл не похож на удостоверение личности')
        else:
            await msg.answer('Произошла ошибка, повторите попытку')
    else:
        msg.answer('Вы не начали отправку файла')


@router.message(F.content_type == ContentType.PHOTO)
async def process_photo(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    if data.get('face') or data.get('back'):
        file_name = f"{PATHS['data']}{'faceside' if data.get('face') else 'backside'}{msg.from_user.id}.png"
        await msg.bot.download(msg.photo[-1], destination=file_name)
        fields = ReadPhoto(file_name, data.get('face'))
        await ReportToAdmin(msg, fields, msg.photo[-1].file_id)
        if fields:
            emptyFields = dict( (k,v) for k, v in fields.items() if v is None)
            notEmptyFields = dict( (k,v) for k, v in fields.items() if v is not None)
            if len(emptyFields)==0:
                await state.clear()
                if data.get('face'):
                    asd = fields|dict((k, v) for k,v in data.items() if k != 'face')
                    asd['fImageId'] = msg.photo[-1].file_id
                    asd['back'] = True
                    await state.update_data(asd)
                    await msg.answer(text='Отправьте обратную сторону удостверения личности')
                else:
                    asd = fields|dict((k, v) for k,v in data.items() if k != 'back')
                    asd['sImageId'] = msg.photo[-1].file_id
                    await state.update_data(asd)

                    await SendToAdmin(msg, 
                                      state, 
                                      GenerateKeyboard({'Изменить':'change', 'Всё верно':'allright'}),
                                      document='NDA')                 
            else:
                await state.clear()
                ndata = notEmptyFields|dict((k,v) for k,v in data.items() if v is not None)
                ndata = data|ndata
                ndata = emptyFields|ndata
                ndata['fImageId' if ndata.get('face') else 'sImageId'] = msg.photo[-1].file_id
                await state.update_data(ndata)
                await msg.answer(text=f'Не найдена информация: {", ".join([i for i in ndata if i not in ["face","back"] and ndata[i] is None])} \nПопробуйте отправить другое фото', 
                                 reply_markup=GenerateKeyboard({'Пропустить':'skip'}))
        else:
            await msg.answer(text='Произола ошибка \nПопробуйте отправить другое фото')
    else:
        await msg.answer(text='Вы не начали отправку фотографии')
        

@router.callback_query(Callback.filter(F.action=='skip'))
async def MainHandler(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if data.get('face'):
        await state.clear()
        await cb.message.edit_text(text='Отправьте фотографию обратной стороны удостверения личности')
        data['back'] = True
        await state.update_data(dict((k, v) for k,v in data.items() if k != 'face'))
    elif data.get('back'):
        await state.update_data(dict((k, v) for k,v in data.items() if k != 'back'))
        await SendToAdmin(cb, 
                          state, 
                          GenerateKeyboard({'Изменить':'change', 'Всё верно':'allright'}),
                          document='NDA')
    await cb.answer()


@router.callback_query(Callback.filter(F.action=='main'))
async def MainHandler(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.answer()
    await cb.message.answer(text='Начните отправку фотографии вашего удостверение личности', reply_markup=GenerateKeyboard({'Начать': 'img'}))
    

@router.callback_query(Callback.filter(F.action=='change'))
async def ChangeHandler(cb: CallbackQuery, state: FSMContext):
    text = cb.message.text
    ntext = ''
    fields = []
    for i in text.split('\n'):
        asd=i.split('-')
        if len(asd)==1:
            await state.update_data(username=list(filter(lambda x:x.count('@'), asd[0].split()))[0].split('@')[-1])
            ntext += i
        else:
            ntext += '\n'
            ntext += f'{asd[0]}\-{f"`{GetMonoText(asd[1])}`" if asd[1] != "нет данных " else GetMonoText(asd[1])}'
            fields.append(asd[0])
        await state.update_data(text=ntext)
    
    await cb.message.edit_text(ntext, reply_markup=GetCheckKeyboard(fields), parse_mode='MarkdownV2')


@router.callback_query(ChangeCallback.filter(F.action=='changeField'))
async def ChangeHandler(cb: CallbackQuery, callback_data: ChangeCallback, state: FSMContext):
    await state.update_data(change=callback_data.field)
    data = await state.get_data()
    await cb.message.edit_text(data['text'], parse_mode='MarkdownV2')
    await cb.message.answer(f'Напишите данные для поля-{callback_data.field}')


@router.callback_query(Callback.filter(F.action=='allright'))
async def OKHandler(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    ndata={}
    for i in data['text'].split('\n'):
        asd=i.split('\-')
        if len(asd)!=1:
            ndata[RemoveMonoText(asd[0])]=RemoveMonoText(asd[1])
    file_name = f"{PATHS['data']}docx{data['username']}.docx"
    GetDocx(file_name, ndata)

    await state.clear()
    await state.update_data(ndata)
    document = FSInputFile(file_name)
    CreateDataFile(ndata, data['username'])

    await cb.message.edit_text(data['text'])
    for i in checker_ids:
        await cb.bot.send_document(i, document)
    await cb.message.answer('Отправить на подпись',
                               reply_markup=InlineKeyboardMarkup(
                               inline_keyboard=[[InlineKeyboardButton(text='Отправить',
                                                                     callback_data=EdoCallback(action='edo',
                                                                                               username=data['username'],
                                                                                               userid=data['userid']).pack())]]))


@router.callback_query(EdoCallback.filter(F.action=='edo'))
async def EdoHandler(cb: CallbackQuery, callback_data: EdoCallback, state: FSMContext):
    data = await state.get_data()
    if data.get('edo_processing'):
        await cb.answer('Предыдущий запрос еще обрабатывается!')
    else:
        link = Main(callback_data.username)

        storageKey = StorageKey(cb.bot.id, callback_data.userid, callback_data.userid)
        opponentState = FSMContext(storage=state.storage, key=storageKey)
        asd = {'data': data }
        await opponentState.update_data(asd)

        await cb.bot.send_message(callback_data.userid, f'Ваши данные были рассмотрены админом \nТеперь вам нужно подписать при помощи ЭЦП документ: \n{link}',
                                  reply_markup=main_actions(callback_data.userid, callback_data.username))
        await cb.message.edit_text('Отправить на подпись')
        await state.clear()
        await state.update_data(edo_processing=True)


@router.message()
async def echo_message(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    if data.get('change'):
        fields = []
        text = data['text'].split('\n')
        for i in range(len(text)):
            asd = text[i].split('-')
            fields.append(asd[0])
            if asd[0]==data['change']:
                text[i] = f"{asd[0]}-{msg.text}"
                break
        text='\n'.join(text)
        await state.update_data(text=text)
    
        if data.get('fImageId'):
            media = []
            photoPaths = [data['fImageId'], data['sImageId']]
            for path in photoPaths:
                media.append(InputMediaPhoto(media=path))
            await msg.answer_media_group(media=media)
        elif data.get('fileName'):
            await msg.answer_document(FSInputFile(data['fileName']))
        else:
            await msg.answer(data['requisites'])
        await msg.answer(text, reply_markup=GetCheckKeyboard(fields))
    # else:
    #     await msg.answer("baaaka")
