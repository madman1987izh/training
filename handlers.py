# -*- coding: utf-8 -*-
import logging
import json
import os
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
from states import RegisterState
from utils import load_data, save_data, is_user_registered, is_child_registered, main_menu, coach_menu

# Список ID тренеров ямаев 1174448948, Заляев 1710633481
COACH_IDS = [1710633481,1174448948]  # Добавьте сюда ID всех тренеров


def register_handlers(router, bot):
    @router.message(Command(commands=['start']))
    async def start(message: types.Message):
        user_registered = is_user_registered(message.from_user.id)

        if message.from_user.id in COACH_IDS:  # Проверка, является ли пользователь тренером
            await message.answer("Добро пожаловать, Тренер! Выберите действие:", reply_markup=coach_menu())
        else:
            await message.answer("Добро пожаловать! Выберите действие:", reply_markup=main_menu(user_registered))

    @router.callback_query(
        lambda c: c.data in ["register", "add_child", "view_profile", "ask_coach", "view_children", "message_parents",
                             "training", "count_sessions"])
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
        elif callback_query.data == "count_sessions":
            data = load_data()
            children_buttons = []

            for parent_id, parent_info in data.items():
                for child in parent_info.get('children', []):
                    children_buttons.append(
                        [InlineKeyboardButton(text=child['child_name'], callback_data=f"count_{child['child_name']}")])

            keyboard = InlineKeyboardMarkup(inline_keyboard=children_buttons)

            await callback_query.message.answer("Выберите ребенка для подсчета занятий:", reply_markup=keyboard)

    @router.callback_query(
        lambda c: c.data.startswith("child_") or c.data.startswith("count_") or c.data == "save_training")
    async def process_training_selection(callback_query: types.CallbackQuery, state: FSMContext):
        try:
            if callback_query.data.startswith("child_"):
                selected_child = callback_query.data.split("_")[1]

                user_data = await state.get_data()
                selected_children = user_data.get('selected_children', [])

                if selected_child not in selected_children:
                    selected_children.append(selected_child)
                    await state.update_data(selected_children=selected_children)

                await callback_query.answer(f"{selected_child} добавлен в список.")

            elif callback_query.data.startswith("count_"):
                selected_child = callback_query.data.split("_")[1]
                current_date_str = datetime.now().strftime("%Y-%m")
                session_count = 0

                # Подсчет количества занятий за текущий месяц
                for filename in os.listdir():
                    if filename.startswith(selected_child) and filename.endswith(".txt"):
                        with open(filename, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if current_date_str in content:
                                session_count += 1

                await callback_query.message.answer(
                    f"Ребенок {selected_child} посетил {session_count} занятий за текущий месяц.")

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
        except Exception as e:
            logging.error(f"Error processing training selection: {e}")
            await callback_query.answer("Произошла ошибка при обработке запроса.")

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
            # Отправка сообщения тренерам
            for coach in COACH_IDS:
                await bot.send_message(coach, f"Вопрос от {parent_name} (ID {user_id}):\n{question}")

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
