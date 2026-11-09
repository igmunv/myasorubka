from aiogram.fsm.state import State, StatesGroup

class FaceControlState(StatesGroup):
    waiting_for_name = State()
    waiting_for_portfolio = State()
    waiting_for_about = State()

class ProjectSubmitState(StatesGroup):
    waiting_for_general_category = State()
    waiting_for_specific_category = State()
    waiting_for_name = State()
    waiting_for_link = State()
    waiting_for_summary = State()
    waiting_for_highlights = State()