from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from config import COMPANIES, CATEGORIES, ADMIN, MODULE_COMPANY
from app.database.requests import create_ticket_from_user_input
from aiogram.filters.state import StateFilter
from app.database.models import Ticket, async_session, Module
from sqlalchemy import select
from datetime import datetime
from zoneinfo import ZoneInfo


import app.keyboards as kb

router = Router()

class Tickets(StatesGroup):
    company_tick = State()  # выбор компании
    type_tick = State()    #выбор типа проблемы
    desc_tick = State()    #описание проблемы
    media_tick = State()   #можно добавить фото/видео
    module_tick = State()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer('Привет! 👋\nЯ бот, созданный для взаимодействия с арендаторами.\nЗдесь вы можете оставить замечания по своему модулю.',
        reply_markup=kb.main)  #конструкция с reply позволяет к овтету бота прикрепить клавиатуру, указаывается конкр. клавиатура из файла keyboards.py, здесь - main

@router.callback_query(F.data == 'ticket')
async def ticket(callback: CallbackQuery, state: FSMContext):
    await state.update_data(user_id=callback.from_user.id)
    await callback.answer('')
    await callback.message.answer('Выберите компанию 🏭', reply_markup=kb.inline_company())
    await state.set_state(Tickets.company_tick)

# Обработчик выбора компании
@router.callback_query(StateFilter(Tickets.company_tick), F.data.in_([str(i) for i in COMPANIES.keys()]))
async def handle_ticket_company(callback: CallbackQuery, state: FSMContext):
    await state.update_data(user_id=callback.from_user.id)
    await callback.answer('')

    company_id = int(callback.data)
    await state.update_data(company_id=company_id)

    if company_id in MODULE_COMPANY:

        async with async_session() as session:
            result = await session.execute(
                select(Module).where(Module.company_id == company_id)
            )
            modules = result.scalars().all()

        await callback.message.edit_text(
            'Выберите модуль:',
            reply_markup=kb.module(modules)
        )
        await state.set_state(Tickets.module_tick)

    else:

        await callback.message.edit_text('Выберите тип замечания 📌', reply_markup=kb.inline_type())
        await state.set_state(Tickets.type_tick)

@router.callback_query(StateFilter(Tickets.module_tick), F.data == "back_company")
async def back_to_company(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text('Выберите компанию 🏭', reply_markup=kb.inline_company())
    await state.set_state(Tickets.company_tick)

# Обработчик выбора модуля компании
@router.callback_query(StateFilter(Tickets.module_tick))
async def handle_ticket_module(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    module_id = int(callback.data)
    await state.update_data(module_id=module_id) 

    async with async_session() as session:
        result = await session.execute(select(Module).where(Module.module_id == module_id))
        module = result.scalar_one_or_none()

    await state.update_data(module_id=module.module_id, module_name=module.name)

    await callback.message.edit_text("Выберите тип замечания 📌", reply_markup=kb.inline_type())

    await state.set_state(Tickets.type_tick)


# Обработчик типа заявок
@router.callback_query(StateFilter(Tickets.type_tick), F.data.in_([str(i) for i in CATEGORIES.keys()]))
async def handle_ticket_type(callback: CallbackQuery, state: FSMContext):
    await state.update_data(user_id=callback.from_user.id)
    await callback.answer('')
    await state.update_data(ticket_type=int(callback.data))
    await callback.message.edit_text('Опишите подробно проблему ✍️', reply_markup=kb.back_type())
    await state.set_state(Tickets.desc_tick)

# Обработчик возврата к выбору типа заявок
@router.callback_query(F.data == "back_type")
async def back_to_type(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text("📌 Выберите тип замечания:", reply_markup=kb.inline_type())
    await state.set_state(Tickets.type_tick)

# Обработчик кнопки "Вернуться к выбору компании"
@router.callback_query(F.data == "back_company")
async def back_to_company(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text("Выберите компанию 🏭", reply_markup=kb.inline_company())
    await state.set_state(Tickets.company_tick)

# Обработчик описания заявки
@router.message(StateFilter(Tickets.desc_tick), F.text)
async def handle_ticket_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    try:
        await message.bot.delete_message(
            chat_id=message.chat.id,
            message_id=message.message_id - 1
        )
    except:
        pass
    await message.answer(
        "Можете приложить фото/видео или нажать на кнопку ниже 'Пропустить'",
        reply_markup=kb.skip_media()
    )
    await state.set_state(Tickets.media_tick)

# Обработчик кнопки "Вернуться к описанию заявки"
@router.callback_query(F.data == "back_desc")
async def back_to_company(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    try:
        await callback.message.delete()
    except:
        pass
    msg = await callback.message.answer('Опишите подробно проблему ✍️')
    await state.set_state(Tickets.desc_tick)
    
    

# Обработчик медиа
@router.message(StateFilter(Tickets.media_tick), F.photo | F.video | F.video_note | F.document)
async def handle_ticket_media(message: Message, state: FSMContext):
    if message.photo:
        media_file_id = message.photo[-1].file_id
    elif message.video:
        media_file_id = message.video.file_id
    elif message.video_note:
        media_file_id = message.video_note.file_id
    elif message.document and message.document.mime_type.startswith("video"):
        media_file_id = message.document.file_id
    else:
        await message.answer("Неподдерживаемый формат медиа, загрузите файл из галереи")
        return

    await state.update_data(media=media_file_id)
    await finish_ticket(message, state)

# Обработчик кнопки"Поопусить" медиа
@router.callback_query(StateFilter(Tickets.media_tick), F.data == "skip_media")
async def skip_media(callback: CallbackQuery, state: FSMContext):
    await state.update_data(user_id=callback.from_user.id)
    await callback.answer()
    await finish_ticket(callback.message, state)

# Функция завершения заявки
async def finish_ticket(message: Message, state: FSMContext):
    from app.database.models import async_session
    from app.database.models import User, Ticket, Media, Status, Ticket_category
    from sqlalchemy import select, insert

    user_data = await state.get_data()
    tg_user = message.from_user

    async with async_session() as session:
        user = await session.get(User, tg_user.id)

        if user is None:
            name_parts=[
                getattr(tg_user, "first_name", "") or "",
                getattr(tg_user, "last_name", "") or ""
            ]
            full_name = "".join (part for part in name_parts if part).strip()
            if not full_name:
                full_name=getattr(tg_user, "username", "")
            user = User(
                user_id=tg_user.id,
                name=full_name,
                phone_number="не указано",
                company_id=int(user_data['company_id'])
            )
            session.add(user)
            await session.flush()

        status = await session.execute(select(Status).where(Status.name == "Новая"))
        status = status.scalar_one()

        ticket = Ticket(
            user_id=user_data["user_id"],
            company_id=int(user_data['company_id']),
            description=user_data['description'],
            status_id=status.status_id,
            data_created=datetime.utcnow(),
            module_id=user_data.get('module_id')
        )
        session.add(ticket)
        await session.flush()

        ticket_id = ticket.ticket_id

        created_at_utc = datetime.utcnow().replace(tzinfo=ZoneInfo("UTC"))
        moscow_tz = ZoneInfo("Europe/Moscow")
        created_at_moscow = created_at_utc.astimezone(moscow_tz)
        created_at_str = created_at_moscow.strftime("%d.%m.%Y %H:%M")


        await session.execute(
            insert(Ticket_category).values(
                ticket_id=ticket.ticket_id,
                category_id=int(user_data['ticket_type'])
            )
        )

        if 'media' in user_data:
            media = Media(
                ticket_id=ticket.ticket_id,
                file_id=user_data['media'],
                file_type="photo" if message.photo else "video"
            )
            session.add(media)

        module_name =""
        if 'module_id' in user_data:
            result = await session.execute(
                select(Module.name).where(Module.module_id==user_data['module_id'])
            )
            module_name = result.scalar_one_or_none() or ""

        await session.commit()

    notify_text = (
        "📩 *Новая заявка*\n"
        f"Номер: {ticket_id}\n"
        f"Дата: {created_at_str}\n"
        f"Компания: {COMPANIES.get(user_data['company_id'])}\n"
        f"Модуль: {module_name if module_name else '-'}\n"        
        f"Тип: {CATEGORIES.get(user_data['ticket_type'])}\n"
        f"Описание: {user_data['description']}"
    )
    if 'media' in user_data:
        notify_text += "\n📎 Есть медиа (фото/видео)"

    for admin_id in ADMIN:
        try:
            if 'media' in user_data:
                if message.photo:
                    await message.bot.send_photo(
                        chat_id=admin_id,
                        photo=user_data['media'],
                        caption=notify_text,
                        parse_mode='Markdown'
                    )
                elif message.video:
                    await message.bot.send_video(
                        chat_id=admin_id,
                        video=user_data['media'],
                        caption=notify_text,
                        parse_mode='Markdown'
                    )
            else:
                await message.bot.send_message(
                    chat_id=admin_id,
                    text=notify_text,
                    parse_mode='Markdown'
            )
        except Exception as e:
            print(f"Ошибка при отправке админу {admin_id}: {e}")
    
    response_text = (
        f"Спасибо! Ваша заявка №{ticket_id} создана:\n\n"
        f"Компания: {COMPANIES.get(user_data['company_id'])}\n"
        + (f"Модуль: {module_name}\n" if module_name else '')
        + f"Тип: {CATEGORIES.get(user_data['ticket_type'])}\n"
        f"Описание: {user_data['description']}\n"
    )
    
    if 'media' in user_data:
        response_text += "\nПриложено медиа"

    response_text += "\n\nЧто вы хотите сделать дальше?"

    await message.answer(response_text, reply_markup=kb.finish_kb())
    await state.clear()
   
@router.callback_query(F.data == "new_ticket")
async def new_ticket(callback: CallbackQuery, state: FSMContext):  
    await state.update_data(user_id=callback.from_user.id)
    await callback.answer()
    await callback.message.answer("Выберите компанию 🏭", reply_markup=kb.inline_company())
    await state.set_state(Tickets.company_tick) 

@router.callback_query(F.data == "end_bot")
async def end_bot(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer("Если захотите снова оставить заявку, просто напишите /start.")










