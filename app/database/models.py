from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy import String, DateTime, ForeignKey, PrimaryKeyConstraint
from typing import List, Optional

engine = create_async_engine('sqlite+aiosqlite:///db.bot_test')
async_session = async_sessionmaker(engine, expire_on_commit=False)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    user_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256))
    phone_number: Mapped[str] = mapped_column(String(256))
    company_id: Mapped[int] = mapped_column(ForeignKey('companies.company_id'))

    tickets: Mapped[List['Ticket']] = relationship(back_populates='user')
    company: Mapped['Company'] = relationship(back_populates='users')

class Ticket(Base):
    __tablename__ = 'tickets'
    ticket_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.user_id'))
    company_id: Mapped[int] = mapped_column(ForeignKey('companies.company_id'))
    module_id: Mapped[Optional[int]] = mapped_column(ForeignKey('modules.module_id'), nullable=True)
    description: Mapped[str] = mapped_column(String(1500))
    status_id: Mapped[int] = mapped_column(ForeignKey('statuses.status_id'))
    data_created: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    comment_adm: Mapped[Optional[str]] = mapped_column(String(1500), nullable=True)

    user: Mapped['User'] = relationship(back_populates='tickets')
    company: Mapped['Company'] = relationship(back_populates='tickets')
    status: Mapped['Status'] = relationship(back_populates='tickets')
    media_files: Mapped[List['Media']] = relationship(back_populates='ticket')
    categories: Mapped[List['Category']] = relationship(secondary='ticket_categories', back_populates='tickets')
    module: Mapped[Optional['Module']] = relationship()

class Company(Base):
    __tablename__ = 'companies'
    company_id: Mapped[int] = mapped_column(primary_key=True)
    company_name: Mapped[str] = mapped_column(String(256))

    users: Mapped[List['User']] = relationship(back_populates='company')
    tickets: Mapped[List['Ticket']] = relationship(back_populates='company')
    modules: Mapped[List['Module']] = relationship(back_populates='company')

class Media(Base):
    __tablename__ = 'media'
    media_id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey('tickets.ticket_id'))
    file_id: Mapped[str] = mapped_column(String(256))
    file_type: Mapped[str] = mapped_column(String(256))
    data_upload: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    ticket: Mapped['Ticket'] = relationship(back_populates='media_files')

class Category(Base):
    __tablename__ = 'categories'
    category_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))

    tickets: Mapped[List['Ticket']] = relationship(secondary='ticket_categories', back_populates='categories')

class Ticket_category(Base):
    __tablename__ = 'ticket_categories'
    category_id: Mapped[int] = mapped_column(ForeignKey('categories.category_id'))
    ticket_id: Mapped[int] = mapped_column(ForeignKey('tickets.ticket_id'))
    __table_args__ = (PrimaryKeyConstraint('category_id', 'ticket_id'),)

class Status(Base):
    __tablename__ = 'statuses'
    status_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

    tickets: Mapped[List['Ticket']] = relationship(back_populates='status')

class Module(Base):
    __tablename__ = 'modules'
    module_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    company_id: Mapped[int] = mapped_column(ForeignKey('companies.company_id'))

    company: Mapped['Company'] = relationship(back_populates='modules')
