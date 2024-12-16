from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import Router
import asyncio
import random

TOKEN = "7434512826:AAG2oyAT9wxbzMcBBN9tTEZGRWHzmJfpAjY"

bot = Bot(token=TOKEN)
storage = MemoryStorage()
router = Router()
dp = Dispatcher(storage=storage)
dp.include_router(router)

# Данные о кроссовках
sneakers = {
    "Мужской": {
        "Nike": {
            "Air Max": {"image": "img/6902299178.jpg", "quantity": 0},
            "Air Force 1": {"image": "images/nike_air_force_1.jpg", "quantity": 0},
            "Jordan": {"image": "img/air-jordan-32-low-bred-AA1256-001.jpg", "quantity": 0}
        },
        "Adidas": {
            "Ultraboost": {"image": "img/adidas-ultraboost-21release-date-price-06.jpg", "quantity": 0},
            "Yeezy": {"image": "img/org.jpg", "quantity": 0},
            "Stan Smith": {"image": "img/adidas-stan-smith-j-m20605-38_1200x.jpg", "quantity": 0}
        },
    },
    "Женский": {
        "Nike": {
            "Air Max": {"image": "img/forcew.jpg", "quantity": 0},
            "Blazer": {"image": "img/jd_175097_b.jpg", "quantity": 0},
            "Cortez": {"image": "img/i.jpg", "quantity": 0}
        },
        "Adidas": {
            "Ultraboost": {"image": "img/ultraboostw.jpg", "quantity": 0},
            "Forum": {"image": "img/airw.jpg", "quantity": 0},
            "Samba": {"image": "img/aq1134_sambarosew_pair-1-e1527796850178.jpg", "quantity": 0}
        },
    },
}
sizes = [str(size) for size in range(36, 46)]

# Состояния
class ShopState(StatesGroup):
    gender = State()
    brand = State()
    model = State()
    size = State()
    confirm = State()

# Функция для создания клавиатуры
def create_keyboard(buttons: list, callback_prefix: str, back_button: str = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for button in buttons:
        builder.button(text=button, callback_data=f"{callback_prefix}_{button}")
    if back_button:
        builder.button(text="Назад", callback_data=back_button)
    builder.adjust(2)
    return builder.as_markup()

# Хендлер команды /start
@router.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    keyboard = create_keyboard(["Мужской", "Женский"], "gender")
    await message.answer("Выберите пол:", reply_markup=keyboard)
    await state.set_state(ShopState.gender)

# Выбор бренда
@router.callback_query(lambda callback: callback.data.startswith("gender"))
async def choose_brand(callback: types.CallbackQuery, state: FSMContext):
    gender = callback.data.split("_")[1]
    await state.update_data(gender=gender)

    keyboard = create_keyboard(list(sneakers[gender].keys()), "brand", back_button="back_start")
    await callback.message.edit_text(f"Вы выбрали: {gender}. Теперь выберите бренд:", reply_markup=keyboard)
    await state.set_state(ShopState.brand)

# Возврат на старт
@router.callback_query(lambda callback: callback.data == "back_start")
async def back_to_start(callback: types.CallbackQuery, state: FSMContext):
    await start(callback.message, state)

# Выбор модели
@router.callback_query(lambda callback: callback.data.startswith("brand"))
async def choose_model(callback: types.CallbackQuery, state: FSMContext):
    brand = callback.data.split("_")[1]
    data = await state.get_data()
    gender = data["gender"]

    await state.update_data(brand=brand)
    models = list(sneakers[gender][brand].keys())

    keyboard = create_keyboard(models, "model", back_button="back_brand")
    await callback.message.edit_text(f"Вы выбрали: {brand}. Теперь выберите модель:", reply_markup=keyboard)
    await state.set_state(ShopState.model)

# Возврат к выбору бренда
@router.callback_query(lambda callback: callback.data == "back_brand")
async def back_to_brand(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    gender = data["gender"]

    keyboard = create_keyboard(list(sneakers[gender].keys()), "brand", back_button="back_start")
    await callback.message.edit_text(f"Вы выбрали: {gender}. Теперь выберите бренд:", reply_markup=keyboard)
    await state.set_state(ShopState.brand)

# Выбор размера (текстовый ввод)
@router.callback_query(lambda callback: callback.data.startswith("model"))
async def ask_size(callback: types.CallbackQuery, state: FSMContext):
    model = callback.data.split("_")[1]
    data = await state.get_data()
    gender = data["gender"]
    brand = data["brand"]

    # Генерация случайного количества
    quantity = random.randint(1, 10)
    sneakers[gender][brand][model]["quantity"] = quantity
    image_path = sneakers[gender][brand][model]["image"]

    await state.update_data(model=model, quantity=quantity)

    from aiogram.types import FSInputFile
    photo = FSInputFile(image_path)
    await callback.message.delete()
    sent_message = await bot.send_photo(
        chat_id=callback.message.chat.id,
        photo=photo,
        caption=(
            f"Вы выбрали модель: {model}.\n"
            f"Осталось в наличии: {quantity} пар.\n"
            "Введите желаемый размер (36–45):"
        )
    )
    await state.update_data(message_id=sent_message.message_id)
    await state.set_state(ShopState.size)

# Обработка текстового ввода размера
@router.message(ShopState.size)
async def handle_size_input(message: types.Message, state: FSMContext):
    size = message.text.strip()
    if size not in sizes:
        await message.answer("Размер должен быть в диапазоне 36–45. Попробуйте снова.")
        return

    data = await state.get_data()
    quantity = data["quantity"]

    if quantity <= 0:
        await message.answer("Извините, выбранная модель распродана.")
        await state.clear()
        return

    await state.update_data(size=size)
    summary = (
        f"Вы выбрали:\n"
        f"Пол: {data['gender']}\n"
        f"Бренд: {data['brand']}\n"
        f"Модель: {data['model']}\n"
        f"Размер: {size}\n"
        f"Осталось пар: {quantity - 1}"
    )
    keyboard = create_keyboard(["Подтвердить", "Отмена"], "confirm")
    await message.answer(summary + "\nПодтвердите покупку:", reply_markup=keyboard)
    await state.set_state(ShopState.confirm)

# Завершение
@router.callback_query(lambda callback: callback.data.startswith("confirm"))
async def finish(callback: types.CallbackQuery, state: FSMContext):
    action = callback.data.split("_")[1]
    if action == "Подтвердить":
        await callback.message.edit_text("Спасибо за покупку! Ожидайте звонка менеджера.")
    else:
        await callback.message.edit_text("Вы отменили покупку.")

    await state.clear()

if __name__ == "__main__":
    async def main():
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)

    asyncio.run(main())
