import sys
sys.path.append('../../') # src/

from bot.exceptions import exceptions_catcher
from bot.utils import respondEvent
from bot.pagination import Paginator

from orders import makeOrderStructure
from generations import getGenerationsScheduleData

from database.tables.orders import getUserOrders, getOrder
from database.tables.generations import getOrderGenerations

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext

import datetime


router = Router(name=__name__)


@router.callback_query(F.data == 'create_order')
@exceptions_catcher()
async def create_order_menu(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()

    message_text = (
        '*🎬 Создание заказа*\n\n'
        '*При оформлении заказа вам нужно будет:*\n'
        '1. Выбрать тематику видео\n'
        '2. Определиться со стилем\n'
        '3. Указать количество уникальных роликов\n'
        '4. Отметить платформы для публикации\n'
        '5. Задать периодичность выхода видео\n'
        '6. Добавить персональный водяной знак (при необходимости)\n\n'
        '‼️ Стоимость зависит исключительно от *числа уникальных видео*\n\n'
        '📅 После оплаты система автоматически *составит график публикаций*\n\n'
        'В назначенный день ролик будет:\n'
        '✔ Сгенерирован\n'
        '✔ Отредактирован\n'
        '✔ Опубликован\n\n'
        '📺 Готовое видео придет вам в виде ссылки'
    )

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='🎥 Начать работу', callback_data='select_video_topic')
    keyboard.button(text='🏠 В главное меню', callback_data='start')
    keyboard.adjust(1)

    kwargs = {
        'text': message_text,
        'parse_mode': 'Markdown',
        'reply_markup': keyboard.as_markup(),
    }

    await respondEvent(
        call, 
        text=message_text, 
        parse_mode="Markdown", 
        reply_markup=keyboard.as_markup()
    )


@router.callback_query(F.data == 'orders')
@exceptions_catcher()
async def orders_menu(call: CallbackQuery) -> None:
    message_text = (
        '*🗂 Мои заказы*\n\n'
        '📁 Выберите интересующий раздел:\n'
        '╭➤ Активные — заказы находящиеся в процессе исполнения.\n'
        '╭➤ Завершённые — полностью выполненные заказы.\n'
    )

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='⏳ Активные', callback_data='orders_list-active-1')
    keyboard.button(text='☑️ Завершённые', callback_data='orders_list-completed-1')
    keyboard.button(text='🏠 В главное меню', callback_data='start')
    keyboard.adjust(2, 1)

    await respondEvent(
        call,
        text=message_text,
        parse_mode="Markdown",
        reply_markup=keyboard.as_markup()
    )


@router.callback_query(F.data.startswith('orders_list'))
@exceptions_catcher()
async def orders_list(call: CallbackQuery) -> None:
    user_id = call.from_user.id

    list_params = call.data.split('-')[1:]
    orders_status = list_params[0]
    list_page = int(list_params[1])

    orders_status_data = {
        'active': {'title': '⏳ Активные заказы', 'is_completed': False},
        'completed': {'title': '✅ Завершённые заказы', 'is_completed': True},
    }

    orders = getUserOrders(user_id, is_completed=orders_status_data[orders_status]['is_completed'])
    orders_buttons = []

    if orders:
        for order in orders:
            order_id = order['id']
            topic = order['data']['topic']
            count = order['data']['count']
            orders_buttons.append({
                'text': f'{count} видео | {topic}',
                'callback_data': f'order_card-{order_id}'
            })

        orders_status_title = orders_status_data[orders_status]['title']
        message_text = (
            f'*{orders_status_title}*\n\n'
            f'🗂 Для получения подробной информации, выберите интересующий заказ.'
        )
    else:
        message_text = (
            f'*{orders_status_title}*\n\n'
            f'Нет ни одного заказа с выбранным статусом.'
        )

    paginator = Paginator(
        array=orders_buttons, 
        offset=5, 
        page_callback=f'orders_list-{orders_status}', 
        back_callback='orders'
    )
    keyboard: InlineKeyboardBuilder = paginator.getPageKeyboard(page=list_page)

    await respondEvent(
        call,
        text=message_text,
        parse_mode="Markdown",
        reply_markup=keyboard.as_markup()
    )


def makeGenerationsSchedule(generations: list) -> str:
    generations_count = len(generations)
    completed_generations_count = 0

    generations_schedule_data: dict = getGenerationsScheduleData(generations)
    generations_dates_list: str = generations_schedule_data['dates_list']
    completed_generations_count: int = generations_schedule_data['completed_generations_count']

    generations_schedule = (
        f'*🎥 Выполнено {completed_generations_count} из {generations_count} запланированных генераций:*\n'
        f'{generations_dates_list}'
    )

    return generations_schedule


@router.callback_query(F.data.startswith('order_card'))
@exceptions_catcher()
async def order_card(call: CallbackQuery) -> None:
    order_id = '-'.join(call.data.split('-')[1:])
    short_order_id = order_id.split('-')[0]

    order: dict | None = getOrder(order_id)
    generations: list = getOrderGenerations(order_id)
    
    keyboard = InlineKeyboardBuilder()

    if order:
        order_data = order['data']

        order_structure = await makeOrderStructure(order_data=order_data)
        generations_schedule = makeGenerationsSchedule(generations)

        message_text = (
            f'*🎬 Заказ #{short_order_id}*\n\n'
            f'🆔 ID заказа: `{order_id}`\n\n'
            f'{order_structure}\n\n'
            f'{generations_schedule}'
        )
    else:
        message_text = '❌ Запрошенный заказ не найден.'
        
    keyboard.button(text='⬅️ Назад', callback_data='orders')
    keyboard.adjust(1)
    
    await respondEvent(
        call,
        text=message_text,
        parse_mode="Markdown",
        reply_markup=keyboard.as_markup(),
    )
