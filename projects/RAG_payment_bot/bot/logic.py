from os import getenv
from sql import check_user_existence
from .templates import MESSAGES
from aiogram.types import Message, LabeledPrice
import re
from llama_index.core import Settings


async def process_buy(message: Message):
    await check_user_existence(message.chat.id)

    PAYMENTS_PROVIDER_TOKEN = getenv("PAYMENTS_PROVIDER_TOKEN")
    PRICE = LabeledPrice(label="Юридический консультант", amount=1000)

    if PAYMENTS_PROVIDER_TOKEN.split(":")[1] == "TEST":
        await message.answer(message.chat.id, MESSAGES["pre_buy_demo_alert"])
        await message.answer_invoice(
            # message.chat.id,
            title=MESSAGES["tm_title"],
            description=MESSAGES["tm_description"],
            provider_token=PAYMENTS_PROVIDER_TOKEN,
            currency="rub",
            photo_url="https://cdn-icons-png.flaticon.com/512/10295/10295637.png",
            photo_height=512,  # !=0/None, иначе изображение не покажется
            photo_width=512,
            photo_size=512,
            is_flexible=False,  # True если конечная цена зависит от способа доставки
            prices=[PRICE],
            start_parameter="test-lawyer-subscription",
            payload="some-invoice-payload-for-our-internal-use",
        )


def extract_prompt_data(store_answer, user_question):
    question = user_question
    _, answer, link, store_file = store_answer.strip().split("\n\n")
    return question, answer, link, store_file


def create_prompt(question, answer):
    prompt = f'Ты нейро-куратор отвечающий на вопросы от пользователя.\nПользователь задает следующий вопрос: "{question}"'
    prompt += f'\nВот овтет пользователю: "{answer}" \nТебе необходимо перефразировать ответ, что бы он соответствовал вопросу. Не придумывай ничего от себя, просто измени слова. Твой ответ должен быть максимально близок к ответу пользователю. Если есть лишняя информация, убери ее.'
    return prompt


def answer_the_question(user_question, query_engine):
    response_from_store = query_engine.query(user_question)
    answer_from_store = re.split(
        r"> Source \(Doc id: .{36}\): ", response_from_store.get_formatted_sources(5000)
    )[1]
    question, answer, link, message_file = extract_prompt_data(
        answer_from_store, user_question
    )
    prompt = create_prompt(question, answer_from_store)
    response = Settings.llm.complete(prompt)
    file_paths = []
    if (
        message_file != "nan"
    ):  # Заложена обработка только фото на данный момент, видео в ответ я не вывожу
        message_file = message_file.split(" ")
        if ~message_file[0].endswith(
            ".ogg"
        ):  # Не обрабатываем .ogg файлы, т.к. это аудиосообщения, их преобразовали в текст.
            for file in message_file:
                file_paths.append("chat/Дайджест/" + file)
    return str(response), file_paths
