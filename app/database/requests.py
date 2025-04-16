from sqlalchemy import select, delete, update
from app.database.models import async_session
from app.database.models import User, Category, Item, Ticket, Order

async def set_user(tg_id: int) -> None:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            session.add(User(tg_id=tg_id))
            await session.commit()

async def get_categories():
    async with async_session() as session:
        return await session.scalars(select(Category))

async def get_category_item(category_id: int):
    async with async_session() as session:
        return await session.scalars(select(Item).where(Item.category == category_id))

async def get_item(item_id: int):
    async with async_session() as session:
        return await session.scalar(select(Item).where(Item.id == item_id))

async def set_ticket(tg_id: int, fio: str, question: str, status: str = 'not_complete'):
    async with async_session() as session:
        session.add(Ticket(tg_id=tg_id, fio=fio, description=question, status=status))
        await session.commit()

async def get_tickets():
    async with async_session() as session:
        return await session.scalars(select(Ticket).where(Ticket.status == 'not_complete'))

async def get_ticket_info(ticket_id: int):
    async with async_session() as session:
        return await session.scalar(select(Ticket).where(Ticket.id == ticket_id))

async def update_ticket_status(ticket_id: int):
    async with async_session() as session:
        await session.execute(
            update(Ticket)
            .where(Ticket.id == ticket_id)
            .values(status='complete')
        )
        await session.commit()

async def set_order(tg_id: int, fio: str, work: str, variant: int, count: int, category: int):
    async with async_session() as session:
        session.add(Order(
            tg_id=tg_id,
            fio=fio,
            work=work,
            variant=variant,
            count=count,
            category=category
        ))
        await session.commit()

async def get_orders():
    async with async_session() as session:
        return await session.scalars(select(Order))

async def get_category(category_id: int):
    async with async_session() as session:
        return await session.scalar(select(Category).where(Category.id == category_id))

async def get_order_info(order_id: int):
    async with async_session() as session:
        return await session.scalar(select(Order).where(Order.id == order_id))

async def del_order(order_id: int):
    async with async_session() as session:
        await session.execute(delete(Order).where(Order.id == order_id))
        await session.commit()