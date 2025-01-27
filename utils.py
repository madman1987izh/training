# -*- coding: utf-8 -*-
import json
from datetime import datetime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = "8086160038:AAGyV5hlS_7KDrwCPFP9CIcOiQJHMkRqTrI"
DATA_FILE = 'data.json'



def load_data():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def is_user_registered(user_id):
    data = load_data()
    return str(user_id) in data

def is_child_registered(user_id, child_name):
    data = load_data()
    return any(child['child_name'] == child_name for child in data.get(str(user_id), {}).get('children', []))

def main_menu(user_registered):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Добавить ребенка", callback_data="add_child")] if user_registered else [InlineKeyboardButton(text="Регистрация", callback_data="register")],
        [InlineKeyboardButton(text="Посмотреть профиль", callback_data="view_profile")],
        [InlineKeyboardButton(text="Задать вопрос тренеру", callback_data="ask_coach")]
    ])
    return keyboard

def coach_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Посмотреть список детей", callback_data="view_children")],
        [InlineKeyboardButton(text="Написать сообщение родителям", callback_data="message_parents")],
        [InlineKeyboardButton(text="Тренировка", callback_data="training")],
        [InlineKeyboardButton(text="Тренировка проведена", callback_data="training_done")]
    ])
    return keyboard