from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram import F, Router, Bot
from app.database import requests as rq
from app import keyboards as kb

router = Router()

class SupportStates(StatesGroup):
    fio = State()
    question = State()

class BuyerStates(StatesGroup):
    work = State()
    fio = State()
    variant = State()

class TicketFormState(StatesGroup):
    id = State()

class OrderAnswerState(StatesGroup):
    answering = State()

admin_ids = [1827788673, 2117456510]

@router.message(CommandStart())
async def cmd_start(message: Message):
    await rq.set_user(message.from_user.id)
    await message.answer('Добро пожаловать в магазин работ', reply_markup=kb.main)

@router.message(F.text == 'Каталог')
async def catalog(message: Message):
    await message.answer('Выберите предмет', reply_markup=await kb.categories())

@router.callback_query(F.data.startswith('category_'))
async def category_items(callback: CallbackQuery):
    category_id = int(callback.data.split('_')[1])
    await callback.message.edit_text(
        'Выберите работу',
        reply_markup=await kb.items(category_id)
    )

@router.callback_query(F.data.startswith('item_'))
async def show_item(callback: CallbackQuery):
    item_id = int(callback.data.split('_')[1])
    item = await rq.get_item(item_id)
    await callback.message.edit_text(
        f'Название: {item.name}\nОписание: {item.description}\nЦена: {item.price}₽',
        reply_markup=kb.buy_work
    )

@router.callback_query(F.data == 'buy')
async def start_order(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BuyerStates.fio)
    await callback.message.answer('Введите ФИО для работы')

@router.message(BuyerStates.fio)
async def process_fio(message: Message, state: FSMContext):
    await state.update_data(fio=message.text)
    await state.set_state(BuyerStates.variant)
    await message.answer('Введите вариант работы (если нет варианта, введите 0)')

@router.message(BuyerStates.variant)
async def process_variant(message: Message, state: FSMContext):
    await state.update_data(variant=message.text)
    await message.answer('Подтвердите заказ', reply_markup=kb.buy_end)

@router.callback_query(F.data == 'buy_payment')
async def confirm_order(callback: CallbackQuery, bot: Bot, state: FSMContext):
    data = await state.get_data()
    await rq.set_order(
        tg_id=callback.from_user.id,
        fio=data['fio'],
        work="Название работы",  # Замените на реальное название
        variant=data['variant'],
        count=1,  # Замените на реальное количество
        category=1  # Замените на реальную категорию
    )
    await callback.message.answer_photo(
        photo='https://imgur.com/a/BHyF2BF',
        caption='Оплата по QR-коду...',
        reply_markup=kb.buy_complete
    )
    for admin_id in admin_ids:
        await bot.send_message(admin_id, 'Новый заказ!')
    await state.clear()

@router.message(F.text == 'Задать вопрос')
async def support(message: Message, state: FSMContext):
    await state.set_state(SupportStates.fio)
    await message.answer('Введите ваше имя и фамилию')

@router.message(SupportStates.fio)
async def process_support_fio(message: Message, state: FSMContext):
    await state.update_data(fio=message.text)
    await state.set_state(SupportStates.question)
    await message.answer('Введите ваш вопрос')

@router.message(SupportStates.question)
async def create_ticket(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await rq.set_ticket(
        tg_id=message.from_user.id,
        fio=data['fio'],
        question=message.text
    )
    await message.answer('Ваш вопрос принят!')
    for admin_id in admin_ids:
        await bot.send_message(admin_id, f'Новый тикет от {data["fio"]}')
    await state.clear()

@router.message(Command('tickets'))
async def admin_tickets(message: Message):
    if message.from_user.id in admin_ids:
        await message.answer('Тикеты:', reply_markup=await kb.admin_support())

@router.callback_query(F.data.startswith('ticket_'))
async def view_ticket(callback: CallbackQuery):
    ticket_id = int(callback.data.split('_')[1])
    ticket = await rq.get_ticket_info(ticket_id)
    await callback.message.edit_text(
        f'Тикет #{ticket_id}\nОт: {ticket.fio}\nВопрос: {ticket.description}',
        reply_markup=kb.ticket_red
    )

@router.callback_query(F.data == 'answer_tick')
async def answer_ticket(callback: CallbackQuery, state: FSMContext):
    await state.set_state(TicketFormState.id)
    await callback.message.answer('Введите ответ:')

@router.message(TicketFormState.id)
async def send_ticket_answer(message: Message, bot: Bot):
    ticket_id = 1  # Здесь должна быть логика получения ID тикета
    await rq.update_ticket_status(ticket_id)
    await message.answer('Ответ отправлен!')

@router.message(Command('orders'))
async def admin_orders(message: Message):
    if message.from_user.id in admin_ids:
        await message.answer('Заказы:', reply_markup=await kb.worker_panel())

@router.callback_query(F.data.startswith('order_'))
async def view_order(callback: CallbackQuery):
    order_id = int(callback.data.split('_')[1])
    order = await rq.get_order_info(order_id)
    await callback.message.edit_text(
        f'Заказ #{order_id}\nКлиент: {order.fio}',
        reply_markup=kb.order_red
    )

@router.callback_query(F.data == 'answer_order')
async def answer_order(callback: CallbackQuery, state: FSMContext):
    await state.set_state(OrderAnswerState.answering)
    await callback.message.answer('Введите ответ:')

@router.message(OrderAnswerState.answering)
async def send_order_answer(message: Message):
    order_id = 1  # Здесь должна быть логика получения ID заказа
    await rq.del_order(order_id)
    await message.answer('Заказ выполнен!')

@router.callback_query(F.data == 'to_main')
async def back_to_main(callback: CallbackQuery):
    await callback.message.answer('Главное меню', reply_markup=kb.main)