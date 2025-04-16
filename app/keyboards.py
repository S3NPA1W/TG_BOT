from aiogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton,
    InlineKeyboardMarkup, 
    InlineKeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.database.requests import (
    get_categories, 
    get_category_item,
    get_tickets,
    get_orders,
    get_category
)

main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Каталог')],
        [KeyboardButton(text='Задать вопрос')]
    ],
    resize_keyboard=True,
    input_field_placeholder='Выберите пункт меню'
)

buy_work = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Купить', callback_data='buy')],
        [InlineKeyboardButton(text='На главную', callback_data='to_main')]
    ]
)

buy_end = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Подтвердить', callback_data='buy_payment')],
        [InlineKeyboardButton(text='На главную', callback_data='to_main')]
    ]
)

buy_complete = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Оплачено', callback_data='buy_completed')]
    ]
)

ticket_red = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Ответить', callback_data='answer_tick')],
        [InlineKeyboardButton(text='Назад', callback_data='to_admin_sup')]
    ]
)

order_red = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Выполнено', callback_data='answer_order')],
        [InlineKeyboardButton(text='Назад', callback_data='to_admin_sup')]
    ]
)

async def categories():
    all_categories = await get_categories()
    keyboard = InlineKeyboardBuilder()
    for category in all_categories:
        keyboard.add(InlineKeyboardButton(
            text=category.name,
            callback_data=f"category_{category.id}"
        ))
    keyboard.add(InlineKeyboardButton(
        text='На главную',
        callback_data='to_main'
    ))
    return keyboard.adjust(2).as_markup()

async def items(category_id: int):
    all_items = await get_category_item(category_id)
    keyboard = InlineKeyboardBuilder()
    for item in all_items:
        keyboard.add(InlineKeyboardButton(
            text=item.name,
            callback_data=f"item_{item.id}"
        ))
    keyboard.add(InlineKeyboardButton(
        text='На главную',
        callback_data='to_main'
    ))
    return keyboard.adjust(2).as_markup()

async def admin_support():
    all_tickets = await get_tickets()
    keyboard = InlineKeyboardBuilder()
    for ticket in all_tickets:
        keyboard.add(InlineKeyboardButton(
            text=f"Тикет #{ticket.id}",
            callback_data=f"ticket_{ticket.id}"
        ))
    keyboard.add(InlineKeyboardButton(
        text='На главную',
        callback_data='to_main'
    ))
    return keyboard.adjust(1).as_markup()

async def worker_panel():
    all_orders = await get_orders()
    keyboard = InlineKeyboardBuilder()
    for order in all_orders:
        category = await get_category(order.category)
        keyboard.add(InlineKeyboardButton(
            text=f"Заказ #{order.id} - {category.name}",
            callback_data=f"order_{order.id}"
        ))
    keyboard.add(InlineKeyboardButton(
        text='На главную',
        callback_data='to_main'
    ))
    return keyboard.adjust(1).as_markup()