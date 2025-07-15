from sqlalchemy import select
from app.database.models import async_session, User, Company, Category, Ticket, Status, Media, Ticket_category
from datetime import datetime

async def create_ticket_from_user_input(
    telegram_user_id: int,
    full_name: str,
    phone_number: str,
    company_name: str,
    category_name: str,
    description: str,
    media_file_id: str = None,
    media_file_type: str = None 
):
    async with async_session() as session:

        company_result = await session.execute(
            select(Company).where(Company.company_name == company_name)
        )
        company = company_result.scalar_one_or_none()
        if not company:
            raise ValueError(f"Компания '{company_name}' не найдена.")

        category_result = await session.execute(
            select(Category).where(Category.name == category_name)
        )
        category = category_result.scalar_one_or_none()
        if not category:
            raise ValueError(f"Категория '{category_name}' не найдена.")

        user_result = await session.execute(
            select(User).where(User.user_id == telegram_user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            user = User(
                user_id=telegram_user_id,
                name=full_name,
                phone_number=phone_number,
                company_id=company.company_id
            )
            session.add(user)
            await session.flush()

        status_result = await session.execute(
            select(Status).where(Status.name == "Новая")
        )
        status = status_result.scalar_one_or_none()
        if not status:
            raise ValueError("Статус 'Новая' не найден.")

        ticket = Ticket(
            user_id=user.user_id,
            company_id=company.company_id,
            description=description,
            status_id=status.status_id,
            data_created=datetime.utcnow()
        )
        session.add(ticket)
        await session.flush()

        ticket_category = Ticket_category(
            ticket_id=ticket.ticket_id,
            category_id=category.category_id
        )
        session.add(ticket_category)

        if media_file_id and media_file_type:
            media = Media(
                ticket_id=ticket.ticket_id,
                file_id=media_file_id,
                file_type=media_file_type,
                data_upload=datetime.utcnow()
            )
            session.add(media)

        await session.commit()
        return ticket.ticket_id
