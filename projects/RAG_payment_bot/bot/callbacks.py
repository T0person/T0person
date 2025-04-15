from aiogram import Router
from aiogram.types import CallbackQuery
from bot import user_modes, process_buy
from sql import check_user_rights
from ui import build_buy_button

callback_router = Router()


@callback_router.callback_query(lambda call: call.data == "buy_subscription")
async def process_buy_callback(call: CallbackQuery):
    await process_buy(call.message)


@callback_router.callback_query(lambda call: call.data == "bm25")
async def response_bm25(callback: CallbackQuery):
    if await check_user_rights(callback.message.chat.id):
        user_modes[callback.message.chat.id] = (
            "bm25"  # Устанавливаем режим "Юридический консультант"
        )
        await callback.message.answer(
            "Теперь вы общаетесь с юридическим консультантом. Введите ваш вопрос."
        )
    else:
        buy_button = build_buy_button("Оформить подписку")
        await callback.message.answer(
            "Для использования бота необходимо оформить платную подписку",
            reply_markup=buy_button.as_markup(),
        )


# Хендлер для выбора нейрокуратора
@callback_router.callback_query(lambda call: call.data == "saiga")
async def response_saiga(callback: CallbackQuery):
    if await check_user_rights(callback.message.chat.id):
        user_modes[callback.message.chat.id] = (
            "saiga"  # Устанавливаем режим "Нейрокуратор"
        )
        await callback.message.answer(
            "Теперь вы общаетесь с нейрокуратором. Введите ваш вопрос."
        )
    else:
        buy_button = build_buy_button("Оформить подписку")
        await callback.message.answer(
            "Для использования бота необходимо оформить платную подписку",
            reply_markup=buy_button.as_markup(),
        )


# Обработчик выбора режима
@callback_router.callback_query(lambda call: call.data in ["bm25", "saiga"])
async def set_user_mode(callback: CallbackQuery):
    # Устанавливаем режим консультанта для пользователя
    user_modes[callback.message.chat.id] = callback.data
    await callback.message.answer(
        f"Выбран режим: {callback.data}. Можете задавать вопросы."
    )
