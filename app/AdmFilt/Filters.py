from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from config import ADMIN

class IsAdmin(BaseFilter):
    def __init__(self):
        self.admin_ids = ADMIN

    async def __call__(self, event: Message | CallbackQuery) -> bool:
        return event.from_user.id in self.admin_ids