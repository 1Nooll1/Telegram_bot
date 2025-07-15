from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton, 
                           InlineKeyboardButton, InlineKeyboardMarkup)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import COMPANIES, CATEGORIES
 
main=InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Оставить замечание 📝', callback_data='ticket')]
]) #создание клавиатуры

def inline_company():
    builder = InlineKeyboardBuilder()
    for company_id, name in COMPANIES.items():
        builder.button(text=name, callback_data=str(company_id))
    builder.adjust(2)
    return builder.as_markup()

def inline_type():
    builder = InlineKeyboardBuilder()
    for code, name in CATEGORIES.items():
        builder.button(text=name, callback_data=str(code))
    builder.button(text="↩️ Вернуться к выбору компании", callback_data='back_company')
    builder.adjust(1)
    return builder.as_markup()

def skip_media():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Пропустить', callback_data='skip_media')],
        [InlineKeyboardButton(text='↩️ Вернуться к описанию проблемы', callback_data='back_desc')]
    ])

def finish_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Создать новую заявку", callback_data="new_ticket")],
        [InlineKeyboardButton(text="Завершить работу с ботом", callback_data="end_bot")]
    ])

def back_type():
    builder = InlineKeyboardBuilder()
    builder.button(text="↩️ Вернуться к выбору типа заявки", callback_data='back_type')
    return builder.as_markup()

def module(modules: list) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=module.name, callback_data=str(module.module_id))]
        for module in modules
    ]
    buttons.append([InlineKeyboardButton(text='↩️ Вернуться к выбору компании', callback_data='back_company')])
    return InlineKeyboardMarkup(inline_keyboard=buttons)