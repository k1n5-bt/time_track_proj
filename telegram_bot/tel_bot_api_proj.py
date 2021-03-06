import logging
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
# db_api import db
from aiogram import Bot, Dispatcher, executor, types
from keyboards import inline
from aiogram.dispatcher.filters import Command
from questions.Test import Test
from telegram_bot.settings_cofiguration import token


logging.basicConfig(level=logging.INFO)

bot = Bot(token=token)
dp = Dispatcher(bot, storage=MemoryStorage())



@dp.message_handler(commands=['start'], state=None)
async def start_message(message: types.Message):
    await message.answer("Привет, я бот для учета времени, я помогу тебе отслеживать твою активность "
                         "в социальных сетях и не только!\n"
                         "Давай начнём, введи /auth для регистрации")
    await Test.DEFAULT.set()


@dp.message_handler(commands=['help'])
async def help_message(message: types.Message):
    await message.answer(
        "Список команд:\n/auth - авторизация в сервисах \n"
        "/starttime - назначить/изменить время начала трекинга\n"
        "/endtime - назначить/изменить время конца трекинга")


@dp.message_handler(Command('auth'), state=Test.DEFAULT)
async def auth(message: types.Message,state:FSMContext):
    await state.update_data(vk_selected=False,github_selected=False,urfu_selected=False)
    await message.answer('Выбери сервисы, которые ты хочешь отслеживать', reply_markup=inline.inline_kb1)
    await Test.SET_SERVICE.set()


@dp.message_handler(Command('nextstep'), state=Test.DEFAULT)
async def next_auth(message: types.Message,state:FSMContext):
    if await inline.get_choosed_keyboard(state) is None:
        #await message.answer('Оставшиеся сервисы:', reply_markup=await inline.get_choosed_keyboard(state))
        #await Test.SET_SERVICE.set()
        await  message.answer('Сервисы закончились, нажми /selecttime\n'
                              'и ты перейдёшь к выбору времени')
        await Test.DEFAULT.set()
    else:
        await message.answer('Оставшиеся сервисы:', reply_markup=await inline.get_choosed_keyboard(state))
        await Test.SET_SERVICE.set()


#VK MESSAGE HANDLERS
@dp.message_handler(state=Test.TAKE_VK_ID)
async def verify_vk_auth(message: types.Message, state: FSMContext):
    await state.update_data(vk_login=message.text)
    await message.answer(text=f'Твоя страница?\n'
                              f'https://vk.com/{message.text}', reply_markup=inline.inline_vk_yes_no_kb)
    await Test.VK_YES.set()



#INLINE_BUTTONS_HANDLERS
@dp.message_handler(state=Test.TAKE_URFU_LOGIN)
async def take_urfu_login(message:types.Message,state:FSMContext):
    await state.update_data(urfu_login=message.text)
    await bot.send_message(message.chat.id,"Теперь введи пароль:")
    await Test.TAKE_URFU_PASSWORD.set()


@dp.message_handler(state=Test.TAKE_URFU_PASSWORD)
async def take_urfu_password(message:types.Message,state:FSMContext):
    async with state.proxy() as data:
        data['urfu_selected']=True
    await state.update_data(urfu_password=message.text)
    await bot.send_message(message.from_user.id, "Отлично! Отправь команду /nextstep\n"
                                                  "для регистрации в следующем сервисе\n"
                                                  "или /selecttime для перехода к выбору\n"
                                                  "времени")
    await Test.DEFAULT.set()

@dp.message_handler(state=Test.TAKE_GITHUB_LOGIN)
async def take_github_login(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['github_selected']=True
    await state.update_data(github_login=message.text)
    await bot.send_message(message.from_user.id, "Отлично! Отправь команду /nextstep\n"
                                                 "для регистрации в следующем сервисе\n"
                                                 "или /selecttime для перехода к выбору\n"
                                                 "времени")
    await Test.DEFAULT.set()


#TIMEHANDLERS
@dp.message_handler(Command('selecttime'), state=Test.DEFAULT)
async def select_track_time(message: types.Message,state:FSMContext):
    await Test.SET_START_TIME.set()
    await message.answer("Выбери начало трекинга!", reply_markup=inline.time_kb)


@dp.message_handler(state=Test.SET_START_TIME)
async def select_start_track_time(message: types.Message,state:FSMContext):
    await message.answer("Теперь выбери конец трекинга!", reply_markup=inline.time_kb)
    async with state.proxy() as data:
        data['start_time']=message.text
    await Test.SET_END_TIME.set()


@dp.message_handler(state=Test.SET_END_TIME)
async def reg_end(message: types.Message,state:FSMContext):
    await message.answer("Отлично теперь мы можем\n"
                         "отслеживать твою активность")
    async with state.proxy() as data:
        data['end_time']=message.text
    all_data=await state.get_data()
    await message.answer(f"""
Твой логин вк:{all_data.get("vk_login")}
Твой логин урфу:{all_data.get("urfu_login")}
Твой логин гитхаб:{all_data.get("github_login")}
Время старта:{all_data.get("start_time")}
Время окончания:{all_data.get("end_time")}
                         """)



    await Test.REGISTERED.set()


# нужно добавить обработчик состояния при сообщении проверять будет по стейту
@dp.callback_query_handler(text_contains='yes', state=Test.VK_YES)
async def success_auth_vk(call: types.CallbackQuery, state:FSMContext):
    async with state.proxy() as data:
        data['vk_selected']=True
    id=await state.get_data()
    x=id.get('vk_login')
    #нужно в конце авторизации определить какую клаву крепить к юзеру
    await bot.send_message(call.from_user.id, "Отлично! Отправь команду /nextstep\n"
                                                 "для регистрации в следующем сервисе\n"
                                                 "или /selecttime для перехода к выбору\n"
                                                 "времени")
    await Test.DEFAULT.set()


@dp.callback_query_handler(text_contains='no', state=Test.VK_YES)
async def unsucces_auth_vk(call: types.CallbackQuery):
    await bot.send_message(call.from_user.id, 'Проверь ник ещё раз, если что-то не так введи данные ещё раз')
    await Test.TAKE_VK_ID.set()


@dp.callback_query_handler(text_contains='urfu', state=Test.SET_SERVICE)
async def set_urfu(call:types.CallbackQuery,state=FSMContext):
    await bot.send_message(chat_id=call.from_user.id,text='Введи свой логин от личного кабинета урфу')
    await Test.TAKE_URFU_LOGIN.set()

@dp.callback_query_handler(text_contains='vk',state=Test.SET_SERVICE)#сделать стейт чтобы много раз не выходило
async def login_vk(call: types.CallbackQuery):
    await bot.send_message(call.from_user.id, "Введи свой id vk или ник.")
    await Test.TAKE_VK_ID.set()


@dp.callback_query_handler(text_contains='github', state=Test.SET_SERVICE)
async def set_github(call:types.CallbackQuery,state=FSMContext):
    await bot.send_message(chat_id=call.from_user.id,text='Введи свой логин или ник в github')
    await Test.TAKE_GITHUB_LOGIN.set()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
