from sql import *
from bot import *
from bot import user_modes
from rag import query_engine, chat_query_engine
from .logic import answer_the_question

from aiogram import F, Router
from aiogram.filters import CommandStart, Command
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram.types import Message, FSInputFile

handler_router = Router()


@handler_router.message(F.successful_payment)
async def successful_payment(message: Message):
    try:
        payment_info = message.successful_payment  # Объект SuccessfulPayment
        total_amount = payment_info.total_amount
        currency = payment_info.currency

        print("SUCCESSFUL PAYMENT:")
        print(f"Total Amount: {total_amount}")
        print(f"Currency: {currency}")

        # Уведомление пользователя
        print("Sending payment confirmation message...")
        await message.answer(
            message.chat.id,
            f"Платеж на сумму {total_amount // 100} {currency} прошел успешно!!!",
        )
        print("Payment confirmation message sent.")

        # Обновление подписки
        print("Updating user subscription...")
        await update_user_subscription(message.chat.id)
        print("User subscription updated.")

        # Проверка после обновления
        print("Checking subscription status...")
        is_active = await check_user_rights(message.chat.id)
        print(f"Subscription active: {is_active}")

    except Exception as e:
        print(f"Error in successful_payment handler: {e}")


# Хэндлер на команду /start
@handler_router.message(CommandStart())
async def cmd_start(message: Message):
    if await check_user_rights(message.chat.id) == False:
        buy_button = build_buy_button("Оформить подписку")
        await message.answer(
            "Для использования бота необходимо оформить платную подписку",
            reply_markup=buy_button.as_markup(),
        )
    else:
        expire_date = await check_user_rights(message.chat.id, True)
        buy_button = build_buy_button("Продлить подписку")
        await message.answer(
            "Ваша подписка истекает " + str(expire_date),
            reply_markup=buy_button.as_markup(),
        )


@handler_router.message(Command("buy"))
async def process_buy_command(message: Message):
    await process_buy(message)


@handler_router.message(
    lambda message: message.text == "/change" or message.chat.id not in user_modes
)
async def response(message: Message):
    if await check_user_rights(message.chat.id):
        change_button = build_change_button()

        await message.answer(
            "Кому задать вопрос?", reply_markup=change_button.as_markup()
        )
    else:
        buy_button = build_buy_button("Оформить подписку")
        await message.answer(
            "Для использования бота необходимо оформить платную подписку",
            reply_markup=buy_button.as_markup(),
        )


# Хендлер для обработки вопросов
@handler_router.message(lambda message: message.chat.id in user_modes)
async def handle_query(message: Message):
    query_type = user_modes.get(message.chat.id)  # Определяем текущий режим
    if query_type == "bm25":
        # Обработка через BM25
        response = query_engine.query(message.text)
        await message.answer(response.response)
    elif query_type == "saiga":
        # Обработка через Saiga
        response, file_paths = answer_the_question(message.text, chat_query_engine)
        if file_paths:
            if len(file_paths) > 1:
                media_group = MediaGroupBuilder()
                for file_path in file_paths:
                    if "video" in file_path:
                        media_group.add(type="video", media=FSInputFile(file_path))
                    else:
                        media_group.add(type="photo", media=FSInputFile(file_path))
                await message.answer_media_group(media_group.build())
                await message.answer(response)
            else:
                file_to_send = FSInputFile(file_paths[0])
                await message.answer_document(file_to_send, caption=response)
        else:
            await message.answer(response)
    else:
        await message.answer(
            "Ошибка: не выбран режим консультанта. Используйте /change для выбора."
        )
