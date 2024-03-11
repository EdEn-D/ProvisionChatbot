from aiogram.fsm.state import StatesGroup, State

class Form(StatesGroup):
    return_response = State()
    rating = State()
    comments = State()

