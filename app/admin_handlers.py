from aiogram import F, Router, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from config import COMPANIES, CATEGORIES, ADMIN
from app.AdmFilt.Filters import IsAdmin
from app.database.models import async_session, Ticket, Status, Module
from app.admin_keyboard import status_change_keyboard
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.notify_user import notify_user_about_status_change
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton, 
                           InlineKeyboardButton, InlineKeyboardMarkup)

import app.admin_keyboard as admin_kb

import re

def escape_markdown(text):
    """
    Экранирует спецсимволы Markdown v1.
    """
    if not text:
        return "-"
    return re.sub(r'([_*\[\]()~`>#+=|{}.!-])', r'\\\1', str(text))


router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

class AdminStates(StatesGroup):
    waiting_for_ticket_id = State()
    waiting_for_status_change = State()

class CommentStates(StatesGroup):
    waiting_for_comment = State()

#Вывод клавиатуры для админа после нажатия кнопки "старт"
@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer('Привет, Админ! 🫡',
        reply_markup=admin_kb.admim_main)

#обработка нажатия на кнопку "Админка"
@router.callback_query(F.data == 'adminka')
async def ticket(callback:CallbackQuery):
    await callback.answer('')
    await callback.message.edit_text('Что хотите сделать?', reply_markup=admin_kb.status_or_report) 





#Обработка действий при нажатии на кнопку "Изменить статус заявки"

#обработка ввода номера заявки
@router.callback_query(F.data == "ticket_change")
async def handle_ticket_change(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите номер заявки")
    await state.set_state(AdminStates.waiting_for_ticket_id)
    await callback.answer()

#если ввели неправил. номер заявки
@router.message(AdminStates.waiting_for_ticket_id)
async def receive_ticket_id(message: Message, state: FSMContext):
    ticket_id = message.text.strip()
    if not ticket_id.isdigit():
        await message.answer("Пожалуйста, введите корректный номер")
        return

    ticket_id = int(ticket_id)

    async with async_session() as session:
        result = await session.execute(
            select(Ticket).options(selectinload(Ticket.status)).filter_by(ticket_id=ticket_id)
        )
        ticket = result.scalar_one_or_none()

        if not ticket:
            await message.answer(f"Заявка с номером {ticket_id} не найдена.")
            return

        await message.answer(
            f"Статус заявки №{ticket_id}: {ticket.status.name}",
            reply_markup=status_change_keyboard(ticket_id)
        )
        await state.set_state(AdminStates.waiting_for_status_change)

#Выбор статуса введенной заявки  
@router.callback_query(F.data.startswith("set_status_"))
async def process_status_change(callback: CallbackQuery, state: FSMContext, bot: Bot):
    
    action, ticket_id_str = callback.data.split(":")
    ticket_id = int(ticket_id_str)

    new_status_name = None
    if action == "set_status_in_progress":
        new_status_name = "В работе"
    elif action == "set_status_completed":
        new_status_name = "Завершена"

    if new_status_name:
        async with async_session() as session:
            
            result = await session.execute(
            select(Ticket)
            .where(Ticket.ticket_id == ticket_id)
            .options(
                selectinload(Ticket.company),
                selectinload(Ticket.categories),
                selectinload(Ticket.status),
                selectinload(Ticket.module),
                selectinload(Ticket.user)
            )
                                       )
            ticket = result.scalar_one_or_none()
            
            old_status=ticket.status.name

            result = await session.execute(select(Status).filter_by(name=new_status_name))
            status_obj = result.scalar_one_or_none()

            ticket.status = status_obj
            await session.commit()

    

        await state.update_data(ticket_id=ticket_id, 
                                original_message_id=callback.message.message_id, 
                                chat_id=callback.message.chat.id,
                                new_status=new_status_name,
                                company_name=ticket.company.company_name,
                                module_name=ticket.module.name if ticket.module else None,
                                category_name=ticket.categories[0].name,
                                description=ticket.description,
                                comment_adm=None,
                                old_status=old_status,
                                changed_by=callback.from_user.full_name or callback.from_user.username
                            )
        
        if new_status_name == "Завершена":
            await callback.message.edit_text(
                text="Статус изменён на 'Завершена'. Хотите добавить комментарий?",
                reply_markup=admin_kb.comment_adm()
            )
        else:
            #уведомление для статусов, если не завершена
            await send_notify_adm(
                bot=callback.bot,
                ticket_id=ticket_id,
                company_name=ticket.company.company_name,
                module_name=ticket.module.module_id if ticket.module else None,
                category_name=ticket.categories[0].name,
                description=ticket.description,
                comment_adm=None,
                old_status=old_status,
                new_status=new_status_name,
                changed_by=callback.from_user.full_name or callback.from_user.username
            )

                    #уведомление пользователю о смене статуса его заявки
            if ticket.user and ticket.user.user_id:
                await notify_user_about_status_change(
                    bot=callback.bot,
                    ticket=ticket,
                    new_status=new_status_name,
                    category_name=ticket.categories[0].name
            )

            

            await callback.message.edit_reply_markup(reply_markup=None)
        await callback.answer()
            

            






#Обработка действий при нажатии на кнопку "Посмотреть информацию по заявке"
#Обработчик кнопки "Посмотреть информацию по заявке"
@router.callback_query(F.data == 'view_ticket')
async def choice_view(callback:CallbackQuery):
    await callback.answer('')
    await callback.message.edit_text("Выберите пункт меню", 
                                  reply_markup=admin_kb.choice_view_ticket()) 
    
#Обработка возврата в админку (главное меню)
@router.callback_query(F.data == "back_admin_menu")
async def ticket(callback:CallbackQuery):
    await callback.answer('')
    await callback.message.edit_text('Что хотите сделать?', reply_markup=admin_kb.status_or_report) 



#Обработчик кнопки "Заявки со статусом новая"
@router.callback_query(F.data == 'view_new')
async def view_new_tickets(callback: CallbackQuery):
    await callback.answer()
    
    async with async_session() as session:
        result = await session.execute(
            select(Ticket)
            .join(Ticket.status)
            .options(selectinload(Ticket.company), selectinload(Ticket.categories))
            .where(Status.name == "Новая")
            .order_by(Ticket.ticket_id)
        )
        tickets = result.scalars().all()

    if not tickets:
        await callback.message.edit_text("Нет заявок со статусом 'Новая'")
        return

    builder = InlineKeyboardBuilder()

    for ticket in tickets:
        company_name = ticket.company.company_name if ticket.company else "Не указано"
        category_name = ticket.categories[0].name if ticket.categories else "Без категории"
        btn_text = f"Заявка №{ticket.ticket_id}, компания - {company_name}, тип - {category_name}"
        builder.button(
            text=btn_text,
            callback_data=f"ticket_{ticket.ticket_id}"
        )

    builder.adjust(1)
    builder.button(text="↩️ Назад в меню", callback_data="back_new_view_menu")

    await callback.message.edit_text("Выберите заявку:", reply_markup=builder.as_markup())    

#Возврат в меню, где выбор статуса заявок
@router.callback_query(F.data == "back_new_view_menu")
async def back_new_view(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text("Введите номер заявки или выберите пункт меню", 
                                  reply_markup=admin_kb.choice_view_ticket()) 

#Обработчик, где выбрана заявка из "Новая" + клава с возможностью поменять статус
@router.callback_query(F.data.startswith("ticket_"))
async def view_ticket_new_details(callback: CallbackQuery):
    ticket_id = int(callback.data.split("_")[1])
    
    async with async_session() as session:
        result = await session.execute(
            select(Ticket)
            .options(
                selectinload(Ticket.company),
                selectinload(Ticket.categories),
                selectinload(Ticket.user),
                selectinload(Ticket.media_files),
                selectinload(Ticket.status),
                selectinload(Ticket.module),
                selectinload(Ticket.user)
            )
            .where(Ticket.ticket_id == ticket_id)
        )
        ticket = result.scalar_one_or_none()

    if not ticket:
        await callback.message.answer("Заявка не найдена")
        return

    company = ticket.company.company_name
    category = ticket.categories[0].name
    user_name = ticket.user.name if ticket.user else "-"
    status = ticket.status.name
    module=ticket.module.module_id if ticket.module else "-"

    text = (
        f"Заявка №{ticket.ticket_id}\n"
        f"\n"
        f"Статус: {status}\n"
        f"Компания: {company}\n"
        f"Модуль: {module}\n"
        f"Тип: {category}\n"
        f"Пользователь: {user_name}\n"
        f"Описание: {ticket.description}"
    )

    #инфо о заявке
    media = ticket.media_files[0] if ticket.media_files else None

    if media:
        try:
            if media.file_type == "photo":
                await callback.message.answer_photo(
                    photo=media.file_id,
                    caption=text
                )
            elif media.file_type == "video":
                await callback.message.answer_video(
                    video=media.file_id,
                    caption=text
                )
        except Exception as e:
            print(f"Ошибка при отправке медиа: {e}")
            await callback.message.answer(text)
    else:
        await callback.message.edit_text(text)

    await callback.message.answer(
        "Выберите действие:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="↩️ Назад к списку", callback_data="back_new")],
            [InlineKeyboardButton(text="Установить статус 'В работе'", 
                                  callback_data=f"seet_status_work:{ticket.ticket_id}")],
            [InlineKeyboardButton(text="Установить статус 'Завершена'", 
                                  callback_data=f"seedt_status_done:{ticket.ticket_id}")]
        ])
    )


#Смена статуса  Новая -> Завершена
@router.callback_query(F.data.startswith("seedt_status_"))
async def update_dticket_status(callback: CallbackQuery, state: FSMContext):
    print("Сработал обработчик смены статуса")
    await callback.answer()

    try:
        action, ticket_id_str = callback.data.split(":")
        ticket_id = int(ticket_id_str)
    except ValueError:
        await callback.message.answer("Некорректные данные.")
        return

    new_status = "Завершена"

    async with async_session() as session:

        status_result = await session.execute(
            select(Status).where(Status.name == new_status)
        )
        status = status_result.scalar_one_or_none()


        result = await session.execute(
            select(Ticket)
            .where(Ticket.ticket_id == ticket_id)
            .options(
                selectinload(Ticket.company),
                selectinload(Ticket.categories),
                selectinload(Ticket.status),
                selectinload(Ticket.module),
                selectinload(Ticket.user)
            )
        )
        ticket = result.scalar_one_or_none()

        old_status = ticket.status.name
        ticket.status_id = status.status_id
        await session.commit()

        #уведомление пользователю о смене статуса его заявки
        if ticket.user and ticket.user.user_id:
            await notify_user_about_status_change(
                bot=callback.bot,
                ticket=ticket,
                new_status=new_status,
                category_name=ticket.categories[0].name
          )

        # Если статус "Завершена"
        if new_status == "Завершена":

            await state.update_data(
                ticket_id=ticket.ticket_id,
                original_message_id=callback.message.message_id,
                chat_id=callback.message.chat.id,
                old_status=old_status,
                new_status=new_status,
                company_name=ticket.company.company_name,
                module_name=ticket.module.name if ticket.module else None,
                category_name=ticket.categories[0].name,
                description=ticket.description,
                changed_by=callback.from_user.full_name or callback.from_user.username
            )

            await callback.message.edit_text(
                text="Статус изменен на 'Завершена'. Хотите добавить комментарий?",
                reply_markup=admin_kb.comment_adm()
            )


#Смена статуса  Новая -> В работе
@router.callback_query(F.data.startswith("seet_status_"))
async def update_ticket_status(callback: CallbackQuery):
    print("Сработал обработчик смены статуса")
    await callback.answer()

    try:
        action, ticket_id_str = callback.data.split(":")
        ticket_id = int(ticket_id_str)
    except ValueError:
        await callback.message.answer("Некорректные данные.")
        return

    new_status = "В работе"

    async with async_session() as session:

        status_result = await session.execute(
            select(Status).where(Status.name == new_status)
        )
        status = status_result.scalar_one_or_none()

        result = await session.execute(
            select(Ticket)
            .where(Ticket.ticket_id == ticket_id)
            .options(
                selectinload(Ticket.company),
                selectinload(Ticket.categories),
                selectinload(Ticket.status),
                selectinload(Ticket.module),
                selectinload(Ticket.user)
            )
        )
        ticket = result.scalar_one_or_none()

        old_status = ticket.status.name
        ticket.status_id = status.status_id
        await session.commit()

        #уведомление пользователю о смене статуса его заявки
        if ticket.user and ticket.user.user_id:
            await notify_user_about_status_change(
                bot=callback.bot,
                ticket=ticket,
                new_status=new_status,
                category_name=ticket.categories[0].name
          )

        await send_notify_adm(
            bot=callback.bot,
            ticket_id=ticket.ticket_id,
            company_name=ticket.company.company_name,
            module_name=ticket.module.name if ticket.module else None,
            category_name=ticket.categories[0].name,
            description=ticket.description,
            comment_adm=ticket.comment_adm,
            old_status=old_status,
            new_status=new_status,
            changed_by=callback.from_user.full_name or callback.from_user.username
        )
        await callback.message.edit_reply_markup(reply_markup=None)

# Обработчик возврата к списку заявок "Новая"
@router.callback_query(F.data == "back_new")
async def back_to_new(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    async with async_session() as session:
        result = await session.execute(
            select(Ticket)
            .join(Ticket.status)
            .options(selectinload(Ticket.company), selectinload(Ticket.categories))
            .where(Status.name == "Новая")
            .order_by(Ticket.ticket_id)
        )
        tickets = result.scalars().all()

    if not tickets:
        await callback.message.answer("Нет заявок со статусом 'Новая'")
        return

    builder = InlineKeyboardBuilder()

    for ticket in tickets:
        company_name = ticket.company.company_name if ticket.company else "Не указано"
        category_name = ticket.categories[0].name if ticket.categories else "Без категории"
        btn_text = f"Заявка №{ticket.ticket_id}, компания - {company_name}, тип - {category_name}"
        builder.button(
            text=btn_text,
            callback_data=f"ticket_{ticket.ticket_id}"
        )

    builder.adjust(1)
    builder.button(text="↩️ Назад в меню", callback_data="back_admin_menu")

    try:
        await callback.message.edit_text("Выберите заявку:", reply_markup=builder.as_markup())
    except Exception:
        await callback.message.answer("Выберите заявку:", reply_markup=builder.as_markup())










#Обработчик кнопки "Заявки со статусом В работе"
@router.callback_query(F.data == 'view_work')
async def view_work_tickets(callback: CallbackQuery):
    await callback.answer()
    
    async with async_session() as session:
        result = await session.execute(
            select(Ticket)
            .join(Ticket.status)
            .options(selectinload(Ticket.company), selectinload(Ticket.categories))
            .where(Status.name == "В работе")
            .order_by(Ticket.ticket_id)
        )
        tickets = result.scalars().all()

    if not tickets:
        await callback.message.edit_text("Нет заявок со статусом 'В работе'")
        return

    builder = InlineKeyboardBuilder()

    for ticket in tickets:
        company_name = ticket.company.company_name if ticket.company else "Не указано"
        category_name = ticket.categories[0].name if ticket.categories else "Без категории"
        btn_text = f"Заявка №{ticket.ticket_id}, компания - {company_name}, тип - {category_name}"
        builder.button(
            text=btn_text,
            callback_data=f"work_ticket_{ticket.ticket_id}"
        )

    builder.adjust(1)
    builder.button(text="↩️ Назад в меню", callback_data="back_work_view_menu")

    await callback.message.edit_text("Выберите заявку:", reply_markup=builder.as_markup())    

#Возврат в меню, где выбор статуса заявок
@router.callback_query(F.data == "back_work_view_menu")
async def back_work_view(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text("Введите номер заявки или выберите пункт меню", 
                                  reply_markup=admin_kb.choice_view_ticket()) 

#Обработчик, где выбрана заявка из списка "В работе"
@router.callback_query(F.data.startswith("work_ticket_"))
async def view_ticket_work_details(callback: CallbackQuery):
    await callback.message.delete()
    ticket_id = int(callback.data.split("_")[-1])
    
    async with async_session() as session:
        result = await session.execute(
            select(Ticket)
            .options(
                selectinload(Ticket.company),
                selectinload(Ticket.categories),
                selectinload(Ticket.user),
                selectinload(Ticket.media_files),
                selectinload(Ticket.status),
                selectinload(Ticket.module),
                selectinload(Ticket.user)
            )
            .where(Ticket.ticket_id == ticket_id)
        )
        ticket = result.scalar_one_or_none()

    if not ticket:
        await callback.message.answer("Заявка не найдена.")
        return

    company = ticket.company.company_name
    category = ticket.categories[0].name
    user_name = ticket.user.name if ticket.user else "Неизвестный пользователь"
    status = ticket.status.name
    module=ticket.module.module_id if ticket.module else "-"

    text = (
        f"Заявка №{ticket.ticket_id}\n"
        f"\n"
        f"Статус: {status}\n"
        f"Компания: {company}\n"
        f"Модуль: {module}\n"
        f"Тип: {category}\n"
        f"Пользователь: {user_name}\n"
        f"Описание: {ticket.description}"
    )

    #инфо о заявке
    media = ticket.media_files[0] if ticket.media_files else None

    if media:
        try:
            if media.file_type == "photo":
                await callback.message.answer_photo(
                    photo=media.file_id,
                    caption=text
                )
            elif media.file_type == "video":
                await callback.message.answer_video(
                    video=media.file_id,
                    caption=text
                )
        except Exception as e:
            print(f"Ошибка при отправке медиа: {e}")
            await callback.message.answer(text)
    else:
        await callback.message.answer(text)

    await callback.message.answer(
        "Выберите действие:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="↩️ Назад к списку", callback_data="back_work")],
            [InlineKeyboardButton(text="Установить статус 'Завершена'", 
                                  callback_data=f"seeet_status_done:{ticket.ticket_id}")]
        ])
    )


#Смена статуса В работе -> Завершено
@router.callback_query(F.data.startswith("seeet_status_"))
async def updatee_ticket_status(callback: CallbackQuery, state: FSMContext):
    print("Сработал обработчик смены статуса")
    await callback.answer()

    try:
        action, ticket_id_str = callback.data.split(":")
        ticket_id = int(ticket_id_str)
    except ValueError:
        await callback.message.answer("Некорректные данные.")
        return

    new_status = "Завершена"

    async with async_session() as session:

        status_result = await session.execute(select(Status).where(Status.name == new_status))
        status = status_result.scalar_one_or_none()

        result = await session.execute(
            select(Ticket)
            .where(Ticket.ticket_id == ticket_id)
            .options(
                selectinload(Ticket.company),
                selectinload(Ticket.categories),
                selectinload(Ticket.status),
                selectinload(Ticket.module),
                selectinload(Ticket.user)
            )
        )
        ticket = result.scalar_one_or_none()

        old_status = ticket.status.name
        ticket.status_id = status.status_id
        await session.commit()

        #уведомление пользователю о смене статуса его заявки
        if ticket.user and ticket.user.user_id:
            await notify_user_about_status_change(
                bot=callback.bot,
                ticket=ticket,
                new_status=new_status,
                category_name=ticket.categories[0].name
          )

        if new_status == "Завершена":

            await state.update_data(
                ticket_id=ticket.ticket_id,
                original_message_id=callback.message.message_id,
                chat_id=callback.message.chat.id,
                old_status=old_status,
                new_status=new_status,
                company_name=ticket.company.company_name,
                module_name=ticket.module.name if ticket.module else None,
                category_name=ticket.categories[0].name,
                description=ticket.description,
                changed_by=callback.from_user.full_name or callback.from_user.username
            )

            await callback.message.edit_text(
                text="Статус изменен на 'Завершена'. Хотите добавить комментарий?",
                reply_markup=admin_kb.comment_adm()
            )




#Если выбран статус "завершена" и нажали кнопку "Хотите добавить комментарий?"
@router.callback_query(F.data == "com_adm")
async def add_comment_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Напишите комментарий к заявке")
    await state.set_state(CommentStates.waiting_for_comment)
    await callback.answer() 

#вывод сообщения, когда заявка со статусом "завершена"
@router.callback_query(F.data == "finish_status")
async def finish_without_comment(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    await send_notify_adm(
        bot=callback.bot,
        ticket_id=data["ticket_id"],
        company_name=data["company_name"],
        module_name=data.get("module_name"),
        category_name=data["category_name"],
        description=data["description"],
        comment_adm=None,
        old_status=data["old_status"],
        new_status=data["new_status"],
        changed_by=data["changed_by"]
    )
    await callback.message.edit_reply_markup(reply_markup=None)

    await state.clear()
    await callback.answer()

#вывод сообщения, когда заявка со статусом "завершена" и есть коммент
@router.message(CommentStates.waiting_for_comment)
async def save_comment(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    ticket_id = data['ticket_id']
    original_message_id = data['original_message_id']
    chat_id = data['chat_id']
    comment_text = message.text

    async with async_session() as session:
        result = await session.execute(
            select(Ticket)
            .options(
                selectinload(Ticket.company),
                selectinload(Ticket.status),
                selectinload(Ticket.categories),
                selectinload(Ticket.module)
            )
            .where(Ticket.ticket_id == ticket_id)
        )
        ticket = result.scalar_one_or_none()

        ticket.comment_adm = comment_text
        await session.commit()

    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)

    await send_notify_adm(
        bot=bot,
        ticket_id=ticket_id,
        company_name=data['company_name'],
        module_name=ticket.module.name if ticket.module else None,
        category_name=data['category_name'],
        description=data['description'],
        comment_adm=comment_text,
        old_status=data['old_status'],
        new_status="Завершена",
        changed_by=data['changed_by']
    )

    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

    await state.clear()


# Обработчик возврата к списку заявок "В работе"
@router.callback_query(F.data == "back_work")
async def back_to_work(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    async with async_session() as session:
        result = await session.execute(
            select(Ticket)
            .join(Ticket.status)
            .options(selectinload(Ticket.company), selectinload(Ticket.categories))
            .where(Status.name == "В работе")
            .order_by(Ticket.ticket_id)
        )
        tickets = result.scalars().all()

    if not tickets:
        await callback.message.answer("Нет заявок со статусом 'Новая'")
        return

    builder = InlineKeyboardBuilder()
    
    for ticket in tickets:
        company_name = ticket.company.company_name if ticket.company else "Не указано"
        category_name = ticket.categories[0].name if ticket.categories else "Без категории"
        btn_text = f"Заявка №{ticket.ticket_id}, компания - {company_name}, тип - {category_name}"
        builder.button(
            text=btn_text,
            callback_data=f"ticket_{ticket.ticket_id}"
        )

    builder.adjust(1)
    builder.button(text="↩️ Назад в меню", callback_data="back_admin_menu")

    await callback.message.edit_text("Выберите заявку:", reply_markup=builder.as_markup())



#Уведомление админов, если изменился статус заявки (+ коммент, если есть и имя исполнителя)    
async def send_notify_adm(bot:Bot, ticket_id: int, company_name: str, category_name:str, description: str, comment_adm: str, old_status:str, new_status: str, changed_by:str, module_name:str = None):

    status_text = (
        "📩 *Изменение статуса заявки*\n"
        f"Номер: {ticket_id}\n"
        f"Cтатус: {escape_markdown(old_status)} -> {escape_markdown(new_status)}\n"
        f"Компания: {escape_markdown(company_name)}\n"
        + (f"Модуль: {escape_markdown(module_name)}\n" if module_name else "")
        + f"Тип: {escape_markdown(category_name)}\n"
        f"Описание: {escape_markdown(description)}\n"
        f"Комментарий: {escape_markdown(comment_adm)}\n"
        f"Кто поменял статус: {escape_markdown(changed_by)}"
)
    
    for admin_id in ADMIN:

                await bot.send_message(
                chat_id=admin_id,
                text=status_text,
                parse_mode='Markdown'
            )