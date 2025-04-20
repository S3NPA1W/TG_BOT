# ========================
# ИМПОРТЫ
# ========================
from sqlalchemy import select, delete, update
from sqlalchemy.orm import joinedload
from app.database.models import async_session
from app.database.models import User, Category, Item, Ticket, Order

# ========================
# РАБОТА С ПОЛЬЗОВАТЕЛЯМИ
# ========================
async def set_user(tg_id: int) -> None:
    """Добавление нового пользователя"""
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            session.add(User(tg_id=tg_id))
            await session.commit()

# ========================
# РАБОТА С КАТЕГОРИЯМИ
# ========================
async def get_categories():
    """Получение всех категорий"""
    async with async_session() as session:
        return await session.scalars(select(Category))

async def get_category(category_id: int):
    """Получение категории по ID"""
    async with async_session() as session:
        return await session.scalar(select(Category).where(Category.id == category_id))

# ========================
# РАБОТА С ТОВАРАМИ
# ========================
async def get_category_items(category_id: int):
    """Получение товаров по категории"""
    async with async_session() as session:
        return await session.scalars(select(Item).where(Item.category_id == category_id))

async def get_item(item_id: int):
    """Получение товара по ID"""
    async with async_session() as session:
        return await session.scalar(select(Item).where(Item.id == item_id))

# ========================
# РАБОТА С ТИКЕТАМИ
# ========================
async def set_ticket(tg_id: int, fio: str, question: str, status: str = 'not_completed'):
    """Создание нового тикета"""
    async with async_session() as session:
        session.add(Ticket(
            tg_id=tg_id,
            fio=fio,
            description=question,
            status=status
        ))
        await session.commit()

async def get_tickets(status: str = 'not_completed'):
    """Получение тикетов по статусу"""
    async with async_session() as session:
        return await session.scalars(select(Ticket).where(Ticket.status == status))

async def get_ticket_info(ticket_id: int):
    """Получение информации о тикете"""
    async with async_session() as session:
        return await session.scalar(select(Ticket).where(Ticket.id == ticket_id))

async def update_ticket_status(ticket_id: int, status: str = 'completed'):
    """Обновление статуса тикета"""
    async with async_session() as session:
        await session.execute(
            update(Ticket)
            .where(Ticket.id == ticket_id)
            .values(status=status)
        )
        await session.commit()

async def save_ticket_answer(ticket_id: int, answer: str):
    """Сохранение ответа на тикет"""
    async with async_session() as session:
        await session.execute(
            update(Ticket)
            .where(Ticket.id == ticket_id)
            .values(answer=answer)
        )
        await session.commit()

# ========================
# РАБОТА С ЗАКАЗАМИ
# ========================
async def set_order(
    tg_id: int,
    fio: str,
    work_id: int,
    variant: str,
    price: int,
    category_id: int,
    status: str = 'new'
):
    """Создание нового заказа"""
    async with async_session() as session:
        order = Order(
            tg_id=tg_id,
            fio=fio,
            work_id=work_id,
            variant=variant,
            price=price,
            category_id=category_id,
            status=status
        )
        session.add(order)
        await session.commit()
        return order.id

async def get_order_with_item(order_id: int):
    """Получение заказа с информацией о товаре"""
    async with async_session() as session:
        result = await session.execute(
            select(Order)
            .join(Item, Order.work_id == Item.id)
            .where(Order.id == order_id)
            .options(joinedload(Order.item))
        )
        return result.scalar_one()

async def get_orders(status: str = None):
    """Получение заказов (с фильтром по статусу)"""
    async with async_session() as session:
        if status:
            return await session.scalars(select(Order).where(Order.status == status))
        return await session.scalars(select(Order))

async def get_order_info(order_id: int):
    """Получение информации о заказе"""
    async with async_session() as session:
        return await session.scalar(select(Order).where(Order.id == order_id))

async def update_order_status(order_id: int, status: str):
    """Обновление статуса заказа"""
    async with async_session() as session:
        await session.execute(
            update(Order)
            .where(Order.id == order_id)
            .values(status=status)
        )
        await session.commit()

async def del_order(order_id: int):
    """Удаление заказа"""
    async with async_session() as session:
        await session.execute(delete(Order).where(Order.id == order_id))
        await session.commit()