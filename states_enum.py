from aiogram.dispatcher.filters.state import State, StatesGroup

class QuestionStates(StatesGroup):
    waiting_for_question = State()
