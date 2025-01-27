from aiogram.fsm.state import StatesGroup, State

class RegisterState(StatesGroup):
    parent_name = State()
    child_name = State()
    phone_number = State()
    question = State()
    message_to_parents = State()
    selected_children = State()