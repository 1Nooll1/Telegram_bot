from aiogram import F, Router, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from config import COMPANIES, CATEGORIES, ADMIN
from app.AdmFilt.Filters import IsAdmin
from app.database.models import async_session, Ticket, Status, Module

from sqlalchemy.future import select
from sqlalchemy.orm import selectinload


async def notify_user_about_status_change(bot: Bot, ticket: Ticket, new_status: str, category_name: str):
        text = (
            f"🔔 Статус вашей заявки №{ticket.ticket_id} изменен.\n\n"
            f"Новый статус: {new_status}\n"
            f"Тип замечания: {category_name}\n"
            f"Описание: {ticket.description}"
        )
        await bot.send_message(chat_id=ticket.user.user_id, text=text)
