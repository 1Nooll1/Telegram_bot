from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton, 
                           InlineKeyboardButton, InlineKeyboardMarkup)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import ADMIN

admim_main=InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Оставить замечание 📝', callback_data='ticket')],
    [InlineKeyboardButton(text='Админка 👮', callback_data='adminka')]
])

status_or_report=InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Изменить статус заявки', callback_data='ticket_change')],
    [InlineKeyboardButton(text='Выгрузить отчет по заявкам', callback_data='export_report')],
    [InlineKeyboardButton(text='Посмотреть информацию по заявке', callback_data='view_ticket')]
])

def status_change_keyboard(ticket_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Установить статус "В работе"', 
                                  callback_data=f"set_status_in_progress:{ticket_id}")],
            [InlineKeyboardButton(text='Установить статус "Завершена"', 
                                  callback_data=f"set_status_completed:{ticket_id}")]
        
    ])

def choice_report():
    return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Выгрузить полный отчет', callback_data='export_full_report')],
            [InlineKeyboardButton(text='Выгрузить отчет в зависимости от статуса', callback_data='report_status')],
            [InlineKeyboardButton(text='Выгрузить отчет в зависимости от компании', callback_data='report_company')],
            [InlineKeyboardButton(text='Выгрузить отчет в зависимости от типа замечания', callback_data='report_category')],
            [InlineKeyboardButton(text='↩️ Вернуться в меню админа', callback_data='back_fr_report')]
    ])

def status_choice_report():
    return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Заявки со статусом "Новая"', callback_data='export_new_report')],
            [InlineKeyboardButton(text='Заявки со статусом "В работе"', callback_data='export_work_report')],
            [InlineKeyboardButton(text='Заявки со статусом "Завершена"', callback_data='export_completed_report')],
            [InlineKeyboardButton(text='↩️ Вернуться к выбору типа отчета', callback_data='back_fr_reportst')]
    ])

def company_choice_report():
    return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Заявки Новатекс', callback_data='novateks_report')],
            [InlineKeyboardButton(text='Заявки ЗДИ', callback_data='zdi_report')],
            [InlineKeyboardButton(text='Заявки Интерскол', callback_data='interskol_report')],
            [InlineKeyboardButton(text='Заявки Сова Моторс Алабуга', callback_data='sova_report')],
            [InlineKeyboardButton(text='Заявки Алтрест', callback_data='altrest_report')],
            [InlineKeyboardButton(text='Заявки Тексфлор', callback_data='teksflor_report')],
            [InlineKeyboardButton(text='↩️ Вернуться к выбору типа отчета', callback_data='back_fr_reportcm')]
    ])

def category_choice_report():
    return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Заявки по "Мелкосрочный ремонт"', callback_data='remont_report')],
            [InlineKeyboardButton(text='Заявки по "Прилегающая территория"', callback_data='territory_report')],
            [InlineKeyboardButton(text='Заявки по "Корректировка систем теплоснабжения"', callback_data='correct_warm_report')],
            [InlineKeyboardButton(text='Заявки по "Водоснабжение/водоотведение"', callback_data='water_report')],
            [InlineKeyboardButton(text='Заявки по "Электроснабжение"', callback_data='power_report')],
            [InlineKeyboardButton(text='Заявки по "Прочее"', callback_data='another_report')],
            [InlineKeyboardButton(text='↩️ Вернуться к выбору типа отчета', callback_data='back_fr_reportct')]
    ])

def choice_view_ticket():
    return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Заявки со статусом "Новая"', callback_data="view_new")],
            [InlineKeyboardButton(text='Заявки со статусом "В работе"', callback_data="view_work")],
            [InlineKeyboardButton(text='↩️ Вернуться в меню админа', callback_data='back_admin_menu')]
    ])

def comment_adm():
    return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Оставить комментарий к заявке', callback_data="com_adm")],
            [InlineKeyboardButton(text='Завершить изменение статуса', callback_data="finish_status")]
    ])