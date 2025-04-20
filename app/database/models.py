# ========================
# ИМПОРТЫ
# ========================
from sqlalchemy import BigInteger, Integer, Text, ForeignKey, Column, String, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
import os, datetime
from dotenv import load_dotenv

load_dotenv()

# ========================
# НАСТРОЙКА БАЗЫ ДАННЫХ
# ========================
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

# ========================
# БАЗОВАЯ МОДЕЛЬ
# ========================
class Base(AsyncAttrs, DeclarativeBase):
    __table_args__ = {'schema': 'tg_bot'}

# ========================
# МОДЕЛЬ ПОЛЬЗОВАТЕЛЯ
# ========================
class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True)

# ========================
# МОДЕЛЬ КАТЕГОРИИ
# ========================
class Category(Base):
    __tablename__ = 'categories'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text)

# ========================
# МОДЕЛЬ ТОВАРА
# ========================
class Item(Base):
    __tablename__ = 'items'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    price: Mapped[int] = mapped_column(Integer)
    category_id: Mapped[int] = mapped_column(ForeignKey('tg_bot.categories.id'))

# ========================
# МОДЕЛЬ ТИКЕТА
# ========================
class Ticket(Base):
    __tablename__ = 'tickets'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger)
    fio: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default='not_complete')

# ========================
# МОДЕЛЬ ЗАКАЗА
# ========================
class Order(Base):
    __tablename__ = 'orders'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger)
    fio: Mapped[str] = mapped_column(String)
    work_id: Mapped[int] = mapped_column(Integer, ForeignKey('tg_bot.items.id'))
    variant: Mapped[str] = mapped_column(String)
    price: Mapped[int] = mapped_column(Integer)
    category_id: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String, default='new')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)
    
    item: Mapped["Item"] = relationship("Item", backref="orders")

# ========================
# ИНИЦИАЛИЗАЦИЯ БД
# ========================
async def init_db():
    """Инициализация базы данных (создание таблиц)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)