# ========================
# ИМПОРТЫ И НАСТРОЙКИ
# ========================
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram import F, Router, Bot
from app.database import requests as rq
from app import keyboards as kb
from os import getenv

router = Router()

# ========================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ========================
def get_admins():
    """Получение списка администраторов из переменных окружения"""
    admins = getenv('ADMIN_ID', '').split(',')
    return [int(admin.strip()) for admin in admins if admin.strip().isdigit()]

# ========================
# КЛАССЫ СОСТОЯНИЙ
# ========================
class SupportStates(StatesGroup):
    """Состояния для формы поддержки"""
    fio = State()
    question = State()

class BuyerStates(StatesGroup):
    """Состояния для оформления заказа"""
    work = State()
    fio = State()
    variant = State()

class TicketFormState(StatesGroup):
    """Состояния для ответа на тикет"""
    answering = State()

class OrderAnswerState(StatesGroup):
    """Состояния для ответа на заказ"""
    answering = State()

# ========================
# ОСНОВНЫЕ КОМАНДЫ
# ========================
@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработка команды /start - регистрация пользователя"""
    await rq.set_user(message.from_user.id)
    await message.answer('Добро пожаловать в магазин работ', reply_markup=kb.main)

@router.message(F.text == 'Каталог')
async def catalog(message: Message):
    """Показ категорий товаров"""
    await message.answer('Выберите предмет', reply_markup=await kb.categories())

# ========================
# ОБРАБОТЧИКИ ТОВАРОВ
# ========================
@router.callback_query(F.data.startswith('category_'))
async def category_items(callback: CallbackQuery):
    """Показ товаров в выбранной категории"""
    category_id = int(callback.data.split('_')[1])
    await callback.message.edit_text(
        'Выберите работу',
        reply_markup=await kb.items(category_id)
    )

@router.callback_query(F.data.startswith('item_'))
async def show_item(callback: CallbackQuery, state: FSMContext):
    """Показ информации о товаре с сохранением ID в состоянии"""
    try:
        item_id = int(callback.data.split('_')[1])
        item = await rq.get_item(item_id)
        if not item:
            await callback.answer("Товар не найден", show_alert=True)
            return
            
        category = await rq.get_category(item.category_id)
        
        # Сохраняем ID товара в состоянии
        await state.update_data(item_id=item_id)
        
        await callback.message.edit_text(
            f'Название: {item.name}\n'
            f'Описание: {item.description}\n'
            f'Категория: {category.name}\n'
            f'Цена: {int(item.price)}₽',
            reply_markup=kb.buy_work
        )
        await callback.answer()
    except Exception as e:
        print(f"Error in show_item: {e}")
        await callback.answer("Ошибка загрузки товара", show_alert=True)

# ========================
# ОФОРМЛЕНИЕ ЗАКАЗА
# ========================
@router.callback_query(F.data == 'buy')
async def start_order(callback: CallbackQuery, state: FSMContext):
    """Начало оформления заказа - получаем ID товара из состояния"""
    try:
        # Получаем данные из состояния
        state_data = await state.get_data()
        item_id = state_data.get('item_id')
        
        if not item_id:
            # Альтернативный способ получения ID, если нет в состоянии
            if hasattr(callback.message.reply_markup, 'inline_keyboard'):
                for row in callback.message.reply_markup.inline_keyboard:
                    for button in row:
                        if button.callback_data and button.callback_data.startswith('item_'):
                            item_id = int(button.callback_data.split('_')[1])
                            break
        
        if not item_id:
            raise ValueError("Не удалось определить ID товара")
            
        item = await rq.get_item(item_id)
        if not item:
            raise ValueError("Товар не найден в базе данных")
            
        await state.update_data(
            item_id=item.id,
            item_name=item.name,
            item_price=item.price,
            item_category=item.category_id
        )
        await state.set_state(BuyerStates.fio)
        await callback.message.answer('Введите ФИО для работы')
        
    except ValueError as ve:
        print(f"Validation error in start_order: {ve}")
        await callback.answer(str(ve), show_alert=True)
    except Exception as e:
        print(f"Unexpected error in start_order: {e}")
        await callback.answer("Произошла ошибка при оформлении заказа", show_alert=True)

@router.message(BuyerStates.fio)
async def process_fio(message: Message, state: FSMContext):
    """Обработка ввода ФИО для заказа"""
    await state.update_data(fio=message.text)
    await state.set_state(BuyerStates.variant)
    await message.answer('Введите вариант работы (если нет варианта, введите 0)')

@router.message(BuyerStates.variant)
async def process_variant(message: Message, state: FSMContext):
    """Обработка ввода варианта работы"""
    await state.update_data(variant=message.text)
    await message.answer('Подтвердите заказ', reply_markup=kb.buy_end)

@router.callback_query(F.data == 'buy_payment')
async def confirm_order(callback: CallbackQuery, bot: Bot, state: FSMContext):
    """Подтверждение и оформление заказа"""
    data = await state.get_data()
    item = await rq.get_item(data['item_id'])
    
    order_id = await rq.set_order(
        tg_id=callback.from_user.id,
        fio=data['fio'],
        work_id=data['item_id'],
        variant=data['variant'],
        price=int(item.price),
        category_id=item.category_id
    )
    
    await callback.message.answer_photo(
        photo='https://imgur.com/a/BHyF2BF',
        caption=f'Оплата работы "{item.name}" по QR-коду...\n'
                f'Цена: {int(item.price)}₽\n'
                f'Номер заказа: {order_id}',
        reply_markup=kb.buy_complete
    )
    
    for admin_id in get_admins():
        await bot.send_message(
            admin_id,
            f'Новый заказ #{order_id}!\n'
            f'ID товара: {data["item_id"]}\n'
            f'Название: {item.name}\n'
            f'Цена: {int(item.price)}₽\n'
            f'Клиент: {data["fio"]}'
        )
    await state.clear()

# ========================
# ПОДДЕРЖКА И ТИКЕТЫ
# ========================
@router.message(F.text == 'Задать вопрос')
async def support(message: Message, state: FSMContext):
    """Начало создания тикета"""
    await state.set_state(SupportStates.fio)
    await message.answer('Введите ваше имя и фамилию')

@router.message(SupportStates.fio)
async def process_support_fio(message: Message, state: FSMContext):
    """Обработка ввода ФИО для тикета"""
    await state.update_data(fio=message.text)
    await state.set_state(SupportStates.question)
    await message.answer('Введите ваш вопрос')

@router.message(SupportStates.question)
async def create_ticket(message: Message, state: FSMContext, bot: Bot):
    """Создание тикета"""
    data = await state.get_data()
    await rq.set_ticket(
        tg_id=message.from_user.id,
        fio=data['fio'],
        question=message.text
    )
    await message.answer('Ваш вопрос принят!')
    for admin_id in get_admins():
        await bot.send_message(admin_id, f'Новый тикет от {data["fio"]}')
    await state.clear()

# ========================
# АДМИН-ПАНЕЛЬ
# ========================
@router.message(Command('tickets'))
async def admin_tickets(message: Message):
    """Показ списка тикетов для администратора"""
    if message.from_user.id in get_admins():
        await message.answer('Тикеты:', reply_markup=await kb.admin_support())

@router.callback_query(F.data.startswith('ticket_'))
async def view_ticket(callback: CallbackQuery, state: FSMContext):
    """Просмотр конкретного тикета"""
    ticket_id = int(callback.data.split('_')[1])
    ticket = await rq.get_ticket_info(ticket_id)
    await state.update_data(ticket_id=ticket_id, user_id=ticket.tg_id)
    await callback.message.edit_text(
        f'Тикет #{ticket_id}\nОт: {ticket.fio}\nВопрос: {ticket.description}',
        reply_markup=kb.ticket_red
    )

@router.callback_query(F.data == 'answer_tick')
async def answer_ticket(callback: CallbackQuery, state: FSMContext):
    """Начало ответа на тикет"""
    await state.set_state(TicketFormState.answering)
    await callback.message.answer('Введите ответ на тикет:')

@router.message(TicketFormState.answering)
async def send_ticket_answer(message: Message, state: FSMContext, bot: Bot):
    """Отправка ответа на тикет"""
    data = await state.get_data()
    ticket_id = data['ticket_id']
    user_id = data['user_id']
    
    await bot.send_message(
        user_id,
        f"Ответ на ваш тикет #{ticket_id}:\n{message.text}"
    )
    
    await rq.update_ticket_status(ticket_id)
    await message.answer('Ответ отправлен пользователю!')
    await state.clear()

@router.message(Command('orders'))
async def admin_orders(message: Message):
    """Показ списка заказов для администратора"""
    if message.from_user.id in get_admins():
        await message.answer('Заказы:', reply_markup=await kb.worker_panel())

@router.callback_query(F.data.startswith('order_'))
async def view_order(callback: CallbackQuery):
    """Просмотр конкретного заказа"""
    order_id = int(callback.data.split('_')[1])
    order = await rq.get_order_with_item(order_id)
    
    await callback.message.edit_text(
        f'Заказ #{order_id}\n'
        f'Товар: {order.item.name}\n'
        f'Цена: {order.price}₽\n'
        f'Клиент: {order.fio}\n'
        f'Вариант: {order.variant}',
        reply_markup=kb.order_red
    )
    await callback.answer()

@router.callback_query(F.data == 'answer_order')
async def answer_order(callback: CallbackQuery, state: FSMContext):
    """Начало ответа на заказ"""
    order_id = int(callback.message.text.split('#')[1].split('\n')[0])
    await state.update_data(order_id=order_id)
    await state.set_state(OrderAnswerState.answering)
    await callback.message.answer('Введите ответ для клиента:')
    await callback.answer()

@router.message(OrderAnswerState.answering)
async def send_order_answer(message: Message, state: FSMContext, bot: Bot):
    """Отправка ответа по заказу"""
    data = await state.get_data()
    order = await rq.get_order_info(data['order_id'])
    
    await bot.send_message(
        order.tg_id,
        f"Ответ по вашему заказу #{data['order_id']}:\n{message.text}"
    )
    
    await rq.update_order_status(data['order_id'], status='completed')
    await message.answer('Ответ отправлен клиенту!')
    await state.clear()

# ========================
# ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ
# ========================
@router.callback_query(F.data == 'to_main')
async def back_to_main(callback: CallbackQuery):
    """Возврат в главное меню"""
    await callback.message.answer('Главное меню', reply_markup=kb.main)