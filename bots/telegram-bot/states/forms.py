from aiogram.fsm.state import State, StatesGroup


class AddProduct(StatesGroup):
    category = State()
    name = State()
    description = State()
    price = State()
    photos = State()
    confirm = State()


class EditProduct(StatesGroup):
    select = State()
    field = State()
    value = State()


class AddCategory(StatesGroup):
    name = State()
    emoji = State()


class AddReview(StatesGroup):
    text = State()
    rating = State()
    photo = State()


class SearchProduct(StatesGroup):
    query = State()


class SetWelcome(StatesGroup):
    photo = State()
    text = State()


class SetContact(StatesGroup):
    text = State()
