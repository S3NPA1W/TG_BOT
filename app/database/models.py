from sqlalchemy import BigInteger, Integer, Text, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
import os
from dotenv import load_dotenv

load_dotenv()

# Подключение к PostgreSQL с увеличенными таймаутами
engine = create_async_engine(
    f"postgresql+asyncpg://"
    f"{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@"
    f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/"
    f"{os.getenv('DB_NAME')}",
    echo=True,
    pool_size=10,
    max_overflow=5,
    pool_timeout=30,
    connect_args={
        "timeout": 30,
        "command_timeout": 30
    }
)

async_session = async_sessionmaker(engine, expire_on_commit=False)

class Base(AsyncAttrs, DeclarativeBase):
    __table_args__ = {'schema': 'tg_bot'}

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True)

class Category(Base):
    __tablename__ = 'categories'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text)

class Item(Base):
    __tablename__ = 'items'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    price: Mapped[int] = mapped_column(Integer)
    category: Mapped[int] = mapped_column(ForeignKey('tg_bot.categories.id'))

class OrderInfo(Base):
    __tablename__ = 'order_info'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user: Mapped[int] = mapped_column(ForeignKey('tg_bot.users.id'))
    item: Mapped[int] = mapped_column(ForeignKey('tg_bot.items.id'))
    variant: Mapped[int] = mapped_column(Integer)

class Ticket(Base):
    __tablename__ = 'tickets'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger)
    fio: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default='not_complete')

class Order(Base):
    __tablename__ = 'orders'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger)
    fio: Mapped[str] = mapped_column(Text)
    work: Mapped[str] = mapped_column(Text)
    variant: Mapped[int] = mapped_column(Integer)
    count: Mapped[int] = mapped_column(Integer)
    category: Mapped[int] = mapped_column(Integer)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)