from sqlalchemy import select
from app.database.models import Company, Category, Status, Module
from config import COMPANIES, CATEGORIES, STATUSES, MODULE_COMPANY

async def initialize_reference_data(session):
    for company_id, company_name in COMPANIES.items():
        result = await session.execute(select(Company).where(Company.company_id == company_id))
        if result.scalar_one_or_none() is None:
            session.add(Company(company_id=company_id, company_name=company_name))

    for category_id, category_name in CATEGORIES.items():
        result = await session.execute(select(Category).where(Category.category_id == category_id))
        if result.scalar_one_or_none() is None:
            session.add(Category(category_id=category_id, name=category_name))

    for status_id, status_name in STATUSES.items():
        result = await session.execute(select(Status).where(Status.status_id == status_id))
        if result.scalar_one_or_none() is None:
            session.add(Status(status_id=status_id, name=status_name))

    for company_id, module_ids in MODULE_COMPANY.items():
        for module_id in module_ids:
            result = await session.execute(select(Module).where(Module.module_id == module_id))
            if result.scalar_one_or_none() is None:
                session.add(Module(
                    module_id=module_id,
                    name=f"Модуль {module_id}",
                    company_id=company_id
                ))
    

    await session.commit()
    print("Данные занесены в БД")
