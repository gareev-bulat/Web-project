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

storage = MemoryStorage()
db_session.global_init("db/blogs.db")

TOKEN = "5137371681:AAGjZMk9EaaQ4RS6FcEdjPv_n-UbAbQry7g"
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=storage)



b1 = KeyboardButton('Войти в аккаунт')
b3 = KeyboardButton('Опубликовать видео [Пока не работает]')

b2 = KeyboardButton('Отмена')

kb_client = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(b1)
kb_client_modern = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(b3)
kb_client_cancel = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(b2)


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


def register_handlers_admin(dp: Dispatcher):
    dp.register_message_handler(command_start, commands=["start", "help"])
    dp.register_message_handler(cancel_handler, Text(equals='Отмена', ignore_case=True), state="*")
    dp.register_message_handler(cm_start_login, Text(equals='Войти в аккаунт', ignore_case=True), state=None)
    dp.register_message_handler(load_email, state=FSMLogin.email)
    dp.register_message_handler(load_password, state=FSMLogin.password)


register_handlers_admin(dp)
executor.start_polling(dp, skip_updates=True)