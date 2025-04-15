from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import types

def build_buy_button(button_text) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text=str(button_text),callback_data="buy_subscription"))
    return builder

def build_change_button() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="Юридическому консультанту", callback_data="bm25"))
    builder.add(types.InlineKeyboardButton(text="Нейрокуратору", callback_data="saiga"))
    return builder