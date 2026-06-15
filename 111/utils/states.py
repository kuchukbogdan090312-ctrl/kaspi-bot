from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    search_user = State()
    give_balance_id = State()
    give_balance_amount = State()
    take_balance_id = State()
    take_balance_amount = State()
    broadcast_text = State()
    broadcast_photo = State()
    edit_plan_price = State()
    edit_plan_desc = State()
    edit_setting = State()


class PaymentStates(StatesGroup):
    waiting_confirm = State()
