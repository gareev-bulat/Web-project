from aiogram import Bot
from aiogram import Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from requests import get
from sql_tables import db_session
from sql_tables.users import User
from sql_tables.videos import Video
import os

storage = MemoryStorage()
db_session.global_init("db/blogs.db")

TOKEN = "5137371681:AAGjZMk9EaaQ4RS6FcEdjPv_n-UbAbQry7g"
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=storage)



b1 = KeyboardButton('Войти в аккаунт')
b3 = KeyboardButton('Опубликовать видео')

b2 = KeyboardButton('Отмена')
b4 = KeyboardButton('Вернуться обратно')

kb_client = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(b1)
kb_client_modern = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(b3)
kb_client_cancel = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(b2)
kb_client_cancel_video = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(b4)


class FSMVideo(StatesGroup):
    name = State()
    preview = State()
    video = State()

async def cm_start_video(message: types.Message):
    await FSMVideo.name.set()
    await message.reply('Введите название для видео.', reply_markup=kb_client_cancel_video)


async def cm_load_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
    await FSMVideo.next()
    await message.reply('Супер! Теперь отправьте фото для превью.', reply_markup=kb_client_cancel_video)


async def cm_load_preview(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['preview'] = message.photo[-1].file_id
        await FSMVideo.next()
        await message.reply('Супер! Теперь отправьте сам видеоролик.', reply_markup=kb_client_cancel_video)
    except Exception as E:
        await message.reply('Что-то пошло не так!', reply_markup=kb_client_modern)


async def cm_load_video(message: types.Video, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['video'] = message.video.file_id
            file = await bot.get_file(message.video.file_id)
            file_path = file.file_path

            file_photo = await bot.get_file(data['preview'])
            file_path_photo = file_photo.file_path

            db_sess = db_session.create_session()
            user = db_sess.query(User).filter(User.telegram_id == message.from_user.id).first()
            count_of_videos = len(os.listdir(f"static//data//channels//{user.id}//videos"))
            video = Video(
                user_id=user.id,
                video_id=count_of_videos,
                video_name=data['name']
            )
            db_sess.add(video)
            db_sess.commit()

            await bot.download_file(file_path, f"static\\data\\channels\\{user.id}\\videos\\{count_of_videos}\\videotitle.mp4")
            await bot.download_file(file_path_photo,
                                    f"static\\data\\channels\\{user.id}\\videos\\{count_of_videos}\\photo.png")
        await message.reply('Супер! Загружаю на видеохостинг ваш ролик, подождите немного :)', reply_markup=kb_client_modern)
        await state.finish()
    except Exception as E:
        await message.reply('Видео слишком большое! Для загрузки его на хостинг вам требуется зайти на сайт.',
                            reply_markup=kb_client_modern)
        await state.finish()
    # except Exception as E:
    #     await message.reply('Что-то пошло не так!', reply_markup=kb_client_modern)
    # await state.finish()


class FSMLogin(StatesGroup):
    email = State()
    password = State()


async def cm_start_login(message: types.Message):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.telegram_id == message.from_user.id).first()
    if user is not None:
        await message.reply('Вы уже вошли в свой аккаунт.', reply_markup=kb_client_modern)
    else:
        await FSMLogin.email.set()
        await message.reply('Введите свою почту', reply_markup=kb_client_cancel)


async def load_email(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['email'] = message.text
    await FSMLogin.next()
    await message.reply('Отлично! Теперь введите пароль.', reply_markup=kb_client_cancel)

async def load_password(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['password'] = message.text

    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.email == data['email']).first()
    temp = user.check_password(data['password'])
    if temp:
        user.telegram_auth = True
        user.telegram_id = message.from_user.id
        # db_sess.add(user)
        db_sess.commit()
        await message.reply('Отлично! Вы зарегистрировались.', reply_markup=kb_client_modern)
    else:
        await message.reply('Что-то пошло не так! Вы ввели неверные данные от своего аккаунта :(', reply_markup=kb_client)
    # con = sqlite3.connect("db/blogs.db")
    # cur = con.cursor()
    # text = f"SELECT * FROM users WHERE email like '{data['email']}' AND WHERE password like '{data['password']}'"
    # result = cur.execute(text).fetchall()
    # print(result)
    await state.finish()




async def load_text_ru(message: types.Message, state: FSMContext):
    params = {"langpair": "en|ru", "q": message.text, "mt": "1", "onlyprivate": "0", "de": "a@b.c"}
    data = get(f"https://translated-mymemory---translation-memory.p.rapidapi.com/api/get", headers=headers, params=params).json()

    await bot.send_message(message.from_user.id, f"Translation: {data['responseData']['translatedText']}", reply_markup=kb_client)
    await state.finish()


async def command_start(message: types.Message):
    await bot.send_message(message.from_user.id, "Добро Пожаловать", reply_markup=kb_client)
    await message.delete()


async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await message.reply('OK', reply_markup=kb_client)


async def cancel_handler_video(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await message.reply('OK', reply_markup=kb_client_modern)


def register_handlers_admin(dp: Dispatcher):
    dp.register_message_handler(command_start, commands=["start", "help"])
    dp.register_message_handler(cancel_handler, Text(equals='Отмена', ignore_case=True), state="*")
    dp.register_message_handler(cancel_handler_video, Text(equals='Вернуться обратно', ignore_case=True), state="*")
    dp.register_message_handler(cm_start_login, Text(equals='Войти в аккаунт', ignore_case=True), state=None)
    dp.register_message_handler(load_email, state=FSMLogin.email)
    dp.register_message_handler(load_password, state=FSMLogin.password)
    dp.register_message_handler(cm_start_video, Text(equals='Опубликовать видео', ignore_case=True), state=None)
    dp.register_message_handler(cm_load_name, state=FSMVideo.name)
    dp.register_message_handler(cm_load_preview, content_types=['photo'], state=FSMVideo.preview)
    dp.register_message_handler(cm_load_video, content_types=['video'], state=FSMVideo.video)

register_handlers_admin(dp)
executor.start_polling(dp, skip_updates=True)