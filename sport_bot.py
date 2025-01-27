import json
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Настройка логирования
logging.basicConfig(level=logging.INFO)

API_TOKEN = "7601827086:AAHcq_cMDtsUSK2zK93fZQ05Y1X7NsInXdo"
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

# Файл для хранения данных
DATA_FILE = 'data.json'


# Загрузка данных из файла
def load_data():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


# Сохранение данных в файл
def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# Проверка регистрации пользователя
def is_user_registered(user_id):
    data = load_data()
    return str(user_id) in data


# Проверка повторной регистрации ребенка
def is_child_registered(user_id, child_name):
    data = load_data()
    return any(child['child_name'] == child_name for child in data.get(str(user_id), {}).get('children', []))


# Состояния для FSM
class RegisterState(StatesGroup):
    parent_name = State()
    child_name = State()
    phone_number = State()
    question = State()
    message_to_parents = State()
    selected_children = State()  # Новое состояние


# Главное меню
def main_menu(user_registered):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Добавить ребенка", callback_data="add_child")] if user_registered else [
            InlineKeyboardButton(text="Регистрация", callback_data="register")],
        [InlineKeyboardButton(text="Посмотреть профиль", callback_data="view_profile")],
        [InlineKeyboardButton(text="Задать вопрос тренеру", callback_data="ask_coach")]
    ])
    return keyboard


# Меню для тренера
def coach_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Посмотреть список детей", callback_data="view_children")],
        [InlineKeyboardButton(text="Написать сообщение родителям", callback_data="message_parents")],
        [InlineKeyboardButton(text="Тренировка", callback_data="training")]  # Новая кнопка
    ])
    return keyboard


# Обработка команды /start
@router.message(Command(commands=['start']))
async def start(message: types.Message):
    user_registered = is_user_registered(message.from_user.id)

    if message.from_user.id == 1710633481:  # ID тренера в телеграме
        await message.answer("Добро пожаловать, Тренер! Выберите действие:", reply_markup=coach_menu())
    else:
        await message.answer("Добро пожаловать! Выберите действие:", reply_markup=main_menu(user_registered))


# Обработка нажатий на кнопки меню
@router.callback_query(
    lambda c: c.data in ["register", "add_child", "view_profile", "ask_coach", "view_children", "message_parents",
                         "training"])
async def process_callback(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data == "register":
        await callback_query.message.answer("Введите ФИО родителя:")
        await state.set_state(RegisterState.parent_name)
    elif callback_query.data == "add_child":
        await callback_query.message.answer("Введите ФИО ребенка:")
        await state.set_state(RegisterState.child_name)
    elif callback_query.data == "view_profile":
        user_id = callback_query.from_user.id
        data = load_data()
        profile = data.get(str(user_id), None)
        if profile:
            children = "\n".join([child['child_name'] for child in profile['children']])
            profile_text = (f"ФИО родителя: {profile['parent_name']}\n"
                            f"Номер телефона: {profile['phone_number']}\n"
                            f"Дети:\n{children}")
        else:
            profile_text = "Профиль не найден."
        await callback_query.message.answer(profile_text)
    elif callback_query.data == "ask_coach":
        await callback_query.message.answer("Введите ваш вопрос для тренера:")
        await state.set_state(RegisterState.question)
    elif callback_query.data == "view_children":
        data = load_data()
        children_list = []

        for parent_id, parent_info in data.items():
            for child in parent_info.get('children', []):
                children_list.append(child['child_name'])

        children_text = "\n".join(children_list) if children_list else "Нет зарегистрированных детей."

        await callback_query.message.answer(f"Список зарегистрированных детей:\n{children_text}")
    elif callback_query.data == "message_parents":
        await callback_query.message.answer("Введите сообщение для всех родителей:")
        await state.set_state(RegisterState.message_to_parents)
    elif callback_query.data == "training":
        data = load_data()
        children_buttons = []

        for parent_id, parent_info in data.items():
            for child in parent_info.get('children', []):
                children_buttons.append(
                    [InlineKeyboardButton(text=child['child_name'], callback_data=f"child_{child['child_name']}")])

        # Добавление кнопки сохранить в конец списка
        children_buttons.append([InlineKeyboardButton(text="Сохранить", callback_data="save_training")])

        keyboard = InlineKeyboardMarkup(inline_keyboard=children_buttons)

        await state.update_data(selected_children=[])

        await callback_query.message.answer("Список детей для тренировки:", reply_markup=keyboard)

    @router.callback_query(lambda c: c.data.startswith("child_") or c.data == "save_training")
    async def process_training_selection(callback_query: types.CallbackQuery, state: FSMContext):
        if callback_query.data.startswith("child_"):
            selected_child = callback_query.data.split("_")[1]

            user_data = await state.get_data()
            selected_children = user_data.get('selected_children', [])

            if selected_child not in selected_children:
                selected_children.append(selected_child)
                await state.update_data(selected_children=selected_children)

            await callback_query.answer(f"{selected_child} добавлен в список.")

        elif callback_query.data == "save_training":
            user_data = await state.get_data()
            selected_children = user_data.get('selected_children', [])

            if selected_children:
                # Сохранение списка выбранных детей в файл с текущей датой
                current_date_str = datetime.now().strftime("%Y-%m-%d")
                with open(f"{current_date_str}.txt", 'w', encoding='utf-8') as f:
                    f.write("\n".join(selected_children))

                # Создание текстового файла для каждого ребенка с датой тренировки
                for child in selected_children:
                    with open(f"{child}_{current_date_str}.txt", 'w', encoding='utf-8') as f:
                        f.write(f"Дата тренировки: {current_date_str}")

                await callback_query.message.answer("Список детей сохранен и файлы созданы.")
                await state.clear()







# Регистрация пользователя
@router.message(StateFilter(RegisterState.parent_name))
async def process_parent_name(message: types.Message, state: FSMContext):
    await state.update_data(parent_name=message.text)
    await message.answer("Введите номер телефона:")
    await state.set_state(RegisterState.phone_number)


@router.message(StateFilter(RegisterState.phone_number))
async def process_phone_number(message: types.Message, state: FSMContext):
    await state.update_data(phone_number=message.text)
    await message.answer("Введите ФИО ребенка:")
    await state.set_state(RegisterState.child_name)


@router.message(StateFilter(RegisterState.child_name))
async def process_child_name(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    user_id = message.from_user.id
    parent_name = user_data.get('parent_name')
    child_name = message.text
    phone_number = user_data.get('phone_number')

    if is_child_registered(user_id, child_name):
        await message.answer("Этот ребенок уже зарегистрирован.")
    else:
        data = load_data()
        if str(user_id) not in data:
            data[str(user_id)] = {'parent_name': parent_name, 'phone_number': phone_number, 'children': []}
        data[str(user_id)]['children'].append({'child_name': child_name})
        save_data(data)
        await message.answer("Регистрация завершена.")
        await state.clear()


@router.message(StateFilter(RegisterState.question))
async def process_question(message: types.Message, state: FSMContext):
    question = message.text
    user_id = message.from_user.id
    user_data = load_data().get(str(user_id), {})

    if user_data:
        parent_name = user_data.get('parent_name', 'Неизвестный пользователь')
        coach_id = 1710633481  # ID тренера в телеграме

        # Отправка сообщения тренеру
        await bot.send_message(coach_id, f"Вопрос от {parent_name} (ID {user_id}):\n{question}")

        # Уведомление пользователя о том, что вопрос отправлен
        await message.answer("Ваш вопрос был отправлен тренеру.")

        # Очистка состояния после отправки вопроса
        await state.clear()


@router.message(StateFilter(RegisterState.message_to_parents))
async def process_message_to_parents(message: types.Message, state: FSMContext):
    message_text = message.text
    data = load_data()

    for parent_id, parent_info in data.items():
        await bot.send_message(parent_id, f"Сообщение от тренера:\n{message_text}")

    await message.answer("Сообщение было отправлено всем родителям.")
    await state.clear()


if __name__ == '__main__':
    dp.run_polling(bot)