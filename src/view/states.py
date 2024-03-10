from aiogram.fsm.state import StatesGroup, State

class Form(StatesGroup):
    awaiting_query = State()
    returning_response = State()
    rating = State()
    notes = State()

