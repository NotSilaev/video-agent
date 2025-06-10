import sys
sys.path.append('../../../') # src/

from config import settings
from logs import addLog
from cache import setCacheValue, getCacheValue, deleteCacheKey

from bot.exceptions import exceptions_catcher
from bot.utils import respondEvent

from orders import makeOrderStructure, processOrder

from aiogram import Bot, Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    ContentType,
    LabeledPrice,
    PreCheckoutQuery
)
from aiogram.filters import Command, StateFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from pathlib import Path
import datetime
import traceback
import json
import uuid


router = Router(name=__name__)


class Order(StatesGroup):
    topic = State()
    style = State()
    count = State()
    platforms = State()
    periodicity = State()
    watermark = State()
    publication_method = State()
    publication_account = State()
    price = State()


@router.callback_query(F.data == 'select_video_topic')
@exceptions_catcher()
async def select_video_topic(call: CallbackQuery, state: FSMContext) -> None:
    message_text = (
        '*🎥 Формирование заказа*\n\n'
        '🚀 Укажите тематику видео.\n\n'
        '💡 Пример: "Инвестиции в криптовалюту"'
    )

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='❌ Отмена заказа', callback_data='create_order')
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

    await state.set_state(Order.topic)


@router.callback_query(F.data == 'select_video_style')
@router.message(Order.topic)
@exceptions_catcher()
async def select_video_style(event: Message | CallbackQuery, state: FSMContext) -> None:
    order_data = await state.get_data()

    # previous step: Save topic
    if isinstance(event, Message):
        topic = event.text.lower()
        await state.update_data(topic=topic)
    elif isinstance(event, CallbackQuery):
        topic = order_data['topic']

    order_data = await state.get_data()
    order_structure = makeOrderStructure(order_data)

    message_text = (
        '*🎥 Формирование заказа*\n\n'
        f'{order_structure}\n\n'
        '👨‍🎨 Укажите стиль видео.\n\n'
        '💡 Пример: "Деловой, тон повествования — спокойный"'
    )

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='⬅️ Назад', callback_data='select_video_topic')
    keyboard.button(text='❌ Отмена заказа', callback_data='create_order')
    keyboard.adjust(2)

    await respondEvent(
        event, 
        text=message_text, 
        parse_mode="Markdown", 
        reply_markup=keyboard.as_markup()
    )

    await state.set_state(Order.style)


@router.callback_query(F.data.startswith('select_video_count'))
@router.message(Order.style)
@exceptions_catcher()
async def select_video_count(event: Message | CallbackQuery, state: FSMContext) -> None:
    order_data = await state.get_data()
    count = 1

    # previous step: Save style
    if isinstance(event, Message):
        style = event.text.lower()
        await state.update_data(style=style)
    elif isinstance(event, CallbackQuery):
        style = order_data['style']
        if '-' in event.data:
            count = int(event.data.split('-')[1])

    # Save count and price
    await state.update_data(count=count)

    price = count * settings.video_cost
    await state.update_data(price=price)

    order_data = await state.get_data()
    order_structure = makeOrderStructure(order_data)

    message_text = (
        '*🎥 Формирование заказа*\n\n'
        f'{order_structure}\n\n'
        '📼 Выберите количество видео.'
    )

    keyboard = InlineKeyboardBuilder()
    
    if count > 1:
        keyboard.button(text='⬅️', callback_data=f'select_video_count-{count-1}')
    else:
        keyboard.button(text='🚩', callback_data=f'#')

    keyboard.button(text=str(count), callback_data='#')

    if count < settings.max_order_video_count:
        keyboard.button(text='➡️', callback_data=f'select_video_count-{count+1}')
    else:
        keyboard.button(text='🏁', callback_data=f'#')

    keyboard.button(text='☑️ Сохранить выбор', callback_data='select_video_platforms')
    keyboard.button(text='⬅️ Назад', callback_data='select_video_style')
    keyboard.button(text='❌ Отмена заказа', callback_data='create_order')
    keyboard.adjust(3, 1, 2)

    await respondEvent(
        event, 
        text=message_text, 
        parse_mode="Markdown", 
        reply_markup=keyboard.as_markup()
    )


@router.callback_query(F.data.startswith('select_video_platforms'))
@exceptions_catcher()
async def select_video_platforms(call: CallbackQuery, state: FSMContext) -> None:
    order_data = await state.get_data()
    count = order_data['count']

    # Save platforms
    try:
        platforms = order_data['platforms']
    except KeyError:
        platforms = []
    
    if '-' in call.data:
        platform = call.data.split('-')[1]
        action = call.data.split('-')[2]
        match action:
            case 'select': platforms.append(platform)
            case 'unselect': platforms.remove(platform)

    await state.update_data(platforms=platforms)

    order_data = await state.get_data()
    order_structure = makeOrderStructure(order_data)
    
    message_text = (
        '*🎥 Формирование заказа*\n\n'
        f'{order_structure}\n\n'
        '📲 Выберите платформы публикации.'
    )

    keyboard = InlineKeyboardBuilder()

    for platform in settings.video_platforms:
        title = platform['title']
        short_title = platform['short_title']
        callback = f'select_video_platforms-{short_title}-select'
        if short_title in platforms:
            title = f'✔️ {title}'
            callback = f'select_video_platforms-{short_title}-unselect'
        keyboard.button(text=title, callback_data=callback)

    if platforms:
        keyboard.button(text='☑️ Сохранить выбор', callback_data='select_video_periodicity')
    keyboard.button(text='⬅️ Назад', callback_data=f'select_video_count-{count}')
    keyboard.button(text='❌ Отмена заказа', callback_data='create_order')
    keyboard.adjust(1, 1, 1, 1, 2)

    await respondEvent(
        call, 
        text=message_text, 
        parse_mode="Markdown", 
        reply_markup=keyboard.as_markup()
    )


@router.callback_query(F.data.startswith('select_video_periodicity'))
@exceptions_catcher()
async def select_video_periodicity(call: CallbackQuery, state: FSMContext) -> None:
    order_data = await state.get_data()
    count = order_data['count']
    periodicity = 1

    # Save periodicity
    if '-' in call.data:
        periodicity = int(call.data.split('-')[1])

    await state.update_data(periodicity=periodicity)

    order_data = await state.get_data()
    order_structure = makeOrderStructure(order_data)
    
    message_text = (
        '*🎥 Формирование заказа*\n\n'
        f'{order_structure}\n\n'
        '📅 Выберите количество публикаций в неделю.'
    )

    keyboard = InlineKeyboardBuilder()
    
    if periodicity > 1:
        keyboard.button(text='⬅️', callback_data=f'select_video_periodicity-{periodicity-1}')
    else:
        keyboard.button(text='🚩', callback_data=f'#')

    keyboard.button(text=str(periodicity), callback_data='#')

    if count > periodicity < 7:
        keyboard.button(text='➡️', callback_data=f'select_video_periodicity-{periodicity+1}')
    else:
        keyboard.button(text='🏁', callback_data=f'#')

    keyboard.button(text='☑️ Сохранить выбор', callback_data='select_video_watermark')
    keyboard.button(text='⬅️ Назад', callback_data=f'select_video_platforms')
    keyboard.button(text='❌ Отмена заказа', callback_data='create_order')
    keyboard.adjust(3, 1, 2)

    await respondEvent(
        call, 
        text=message_text, 
        parse_mode="Markdown", 
        reply_markup=keyboard.as_markup()
    )


@router.callback_query(F.data.startswith('select_video_watermark'))
@exceptions_catcher()
async def select_video_watermark(call: CallbackQuery, state: FSMContext) -> None:
    order_data = await state.get_data()
    periodicity = order_data['periodicity']

    order_structure = makeOrderStructure(order_data)
    
    message_text = (
        '*🎥 Формирование заказа*\n\n'
        f'{order_structure}\n\n'
        '🖼 Отправьте любое изображение, которое хотите использовать в качестве водяного знака.\n\n'
        '‼️ Не требуется самостоятельно настраивать прозрачность картинки — система сделает это за Вас.'
    )

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='⏩ Пропустить', callback_data='select_video_publication_method')
    keyboard.button(text='⬅️ Назад', callback_data=f'select_video_periodicity-{periodicity}')
    keyboard.button(text='❌ Отмена заказа', callback_data='create_order')
    keyboard.adjust(1, 2)

    await respondEvent(
        call, 
        text=message_text, 
        parse_mode="Markdown", 
        reply_markup=keyboard.as_markup()
    )

    await state.set_state(Order.watermark)


@router.callback_query(F.data.startswith('select_video_publication_method'))
@router.message(F.photo)
@router.message(Order.watermark)
@exceptions_catcher()
async def select_video_publication_method(event: Message | CallbackQuery, state: FSMContext, bot: Bot) -> None:
    watermark_path = None
    watermark_status = 'не добавлен'

    publication_method = None
    publication_methods = [
        {'id': 'manual', 'title': 'Ручной'},
        {'id': 'auto', 'title': 'Автоматический'},
        {'id': 'independent', 'title': 'Самостоятельный'},
    ]

    # previous step: Save watermark
    if isinstance(event, Message):
        if event.photo:
            photo = event.photo[-1]
            file_id = photo.file_id
            file = await bot.get_file(file_id)
            file_path = file.file_path
            file_name = f"{file_id}.jpg"
            watermarks_dir = Path(r"media\watermarks")
            watermarks_dir.mkdir(parents=True, exist_ok=True)
            watermark_path = rf"{watermarks_dir}\{file_name}"
            await bot.download_file(file_path, watermark_path)
            watermark_status = 'добавлен'
    # Save publication method
    elif isinstance(event, CallbackQuery):
        if '-' in event.data:
            publication_method = event.data.split('-')[1]

    await state.update_data(watermark=watermark_path)
    await state.update_data(publication_method=publication_method)

    order_data = await state.get_data()
    order_structure = makeOrderStructure(order_data)
    
    message_text = (
        '*🎥 Формирование заказа*\n\n'
        f'{order_structure}\n\n'
        '📤 Выберите способ публикации видео:\n'
        '╭➤ Ручной — публикация с предварительной модерацией администратором.\n'
        '╭➤ Автоматический — моментальная, программная публикация, сразу после генерации видео.\n'
        '╭➤ Самостоятельный — Вы получите готовое видео сразу после генерации для самостоятельного размещения на платформах.\n\n'
        '‼️ При выборе автоматического метода публикации, видео будет опубликовано без музыки из-за ограничений платформ.'
    )

    keyboard = InlineKeyboardBuilder()

    for method in publication_methods:
        method_id = method['id']
        method_title = method['title']
        callback_data = f'select_video_publication_method-{method_id}'
        if publication_method == method_id:
            method_title = f'✔️ {method_title}'
            callback_data = '#'

        keyboard.button(text=method_title, callback_data=callback_data)

    if publication_method:
        match publication_method:
            case 'manual': callback_data = 'select_video_publication_account'
            case 'auto': callback_data = 'check_order'
            case 'independent': callback_data = 'check_order'
        keyboard.button(text='☑️ Сохранить выбор', callback_data=callback_data)

    keyboard.button(text='⬅️ Назад', callback_data=f'select_video_watermark')
    keyboard.button(text='❌ Отмена заказа', callback_data='create_order')
    keyboard.adjust(3, 1, 2)

    await respondEvent(
        event, 
        text=message_text, 
        parse_mode="Markdown", 
        reply_markup=keyboard.as_markup()
    )


@router.callback_query(F.data.startswith('select_video_publication_account'))
@exceptions_catcher()
async def select_video_publication_account(call: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    publication_account = None
    publications_accounts = [
        {'id': 'client', 'title': 'Клиентский'},
        {'id': 'service', 'title': 'Сервисный'},
    ]

    if '-' in call.data:
        publication_account = call.data.split('-')[1]

    await state.update_data(publication_account=publication_account)

    order_data = await state.get_data()
    publication_method = order_data['publication_method']

    order_data = await state.get_data()
    order_structure = makeOrderStructure(order_data)
    
    message_text = (
        '*🎥 Формирование заказа*\n\n'
        f'{order_structure}\n\n'
        '📺 Выберите на чей аккаунт будет опубликовано видео:\n'
        '╭➤ Клиентский — публикация видео на Ваш аккаунт.\n'
        '╭➤ Сервисный — публикация видео на аккаунт сервиса.\n\n'
        '‼️ При выборе варианта: "Клиентский" с Вами свяжется администратор для получения API-ключей или логина/пароля от аккаунта.'
    )

    keyboard = InlineKeyboardBuilder()

    for account in publications_accounts:
        account_id = account['id']
        account_title = account['title']
        callback_data = f'select_video_publication_account-{account_id}'
        if publication_account == account_id:
            account_title = f'✔️ {account_title}'
            callback_data = '#'
        keyboard.button(text=account_title, callback_data=callback_data)

    if publication_account:
        keyboard.button(text='☑️ Сохранить выбор', callback_data='check_order')

    keyboard.button(text='⬅️ Назад', callback_data=f'select_video_publication_method-{publication_method}')
    keyboard.button(text='❌ Отмена заказа', callback_data='create_order')
    keyboard.adjust(2, 1, 2)

    await respondEvent(
        call, 
        text=message_text, 
        parse_mode="Markdown", 
        reply_markup=keyboard.as_markup()
    )
    

@router.callback_query(F.data == 'check_order')
@exceptions_catcher()
async def check_order(event: Message | CallbackQuery, state: FSMContext, bot: Bot) -> None:
    order_data = await state.get_data()
    try:
        publication_account = order_data['publication_account']
        back_callback = f'select_video_publication_account-{publication_account}'
    except KeyError:
        publication_method = order_data['publication_method']
        back_callback = f'select_video_publication_method-{publication_method}'

    order_data = await state.get_data()
    order_structure = makeOrderStructure(order_data)
    
    message_text = (
        '*🎥 Формирование заказа*\n\n'
        f'{order_structure}\n\n'
        '✅ Формирование заказа завершено. *Проверьте правильность заполнения параметров* и получите счёт на оплату.'
    )

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='🧾 Получить счёт', callback_data=f'get_order_invoice')
    keyboard.button(text='⬅️ Назад', callback_data=back_callback)
    keyboard.button(text='❌ Отмена заказа', callback_data='create_order')
    keyboard.adjust(1, 2)

    await respondEvent(
        event, 
        text=message_text, 
        parse_mode="Markdown", 
        reply_markup=keyboard.as_markup()
    )


@router.callback_query(F.data.startswith('get_order_invoice'))
@exceptions_catcher()
async def get_order_invoice(call: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    chat_id = call.message.chat.id
    user_id = call.from_user.id

    # Remove previous bot message
    bot_message_id = call.message.message_id
    await bot.delete_message(chat_id=chat_id, message_id=bot_message_id)

    order_data = await state.get_data()
    price = order_data['price']

    order_structure = makeOrderStructure(order_data)
    
    # Save invoice data in cache
    try:
        invoice_id = f'invoice-{uuid.uuid4()}'
        invoice_data = json.dumps({
            'chat_id': chat_id,
            'user_id': user_id,
            'order_data': order_data,
        })  
        
        setCacheValue(
            key=invoice_id,
            value=invoice_data,
            expire=60*30, # 30 mins
        )
    except Exception as e:
        addLog(
            level='ERROR',
            text=f'[Error during invoice data saving in cache]: {e}\n\nTraceback: {traceback.format_exc()}'
        )

    # Send invoice to user
    description_text = (
        f'{order_structure}\n\n'
        'Оплатите счёт в течение 30 минут'
    )

    try:
        invoice_message = await bot.send_invoice(
            chat_id=chat_id,
            title=f'Оплата заказа',
            description=description_text,
            payload=invoice_id,
            currency='XTR',
            prices=[{
                'label': 'Оплата заказа',
                'amount': price,
            }],
            protect_content=True,
        )

        setCacheValue(
            key=f'invoice_message-{invoice_id}',
            value=invoice_message.message_id,
            expire=60*30, # 30 mins
        )

        await state.clear()
    except Exception as e:
        addLog(
            level='ERROR',
            text=f'[Error during invoice sending]: {e}\n\nTraceback: {traceback.format_exc()}'
        )


@router.pre_checkout_query()
async def order_prechekout_handler(pre_checkout_query: PreCheckoutQuery, bot: Bot) -> None:
    "Payment pre-checkhout handler."

    try:
        invoice_id = pre_checkout_query.invoice_payload
        invoice_data = getCacheValue(key=invoice_id)

        if invoice_data:
            await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
        else:
            await bot.answer_pre_checkout_query(
                pre_checkout_query.id, 
                ok=False, 
                error_message='Время оплаты счёта истекло.'
            )
    except Exception as e:
        addLog(
            level='ERROR',
            text=f'[Error during payment preprocessing]: {e}\n\nTraceback: {traceback.format_exc()}'
        )


@router.message(F.content_type == ContentType.SUCCESSFUL_PAYMENT)
async def order_successful_payment_handler(message: Message, bot: Bot) -> None:
    "Successful payment handler."

    user_id = message.from_user.id

    try:
        invoice_id = message.successful_payment.invoice_payload
        invoice_data = json.loads(getCacheValue(key=invoice_id))

        # Remove the bot invoce message
        invoice_message_id = getCacheValue(f'invoice_message-{invoice_id}')
        await bot.delete_message(chat_id=invoice_data['chat_id'], message_id=invoice_message_id)

        # Sending a message about a successful payment
        order_data = invoice_data['order_data']
        order_structure = makeOrderStructure(order_data)
    
        message_text = (
            '*✅ Заказ успешно оплачен, составляем график публикаций.*\n\n'
            f'{order_structure}\n\n'
            f'📅 Платёж проведён: *{datetime.datetime.now()}*'
        )

        await message.answer(
            text=message_text,
            parse_mode='Markdown',
        )

        # Process order
        processOrder(user_id, order_data)

        if settings.dev_mode:
            refund_payment = True
        else:
            refund_payment = False

    except Exception as e:
        refund_payment = True

        addLog(
            level='CRITICAL',
            text=f'[Error when processing an already paid invoice]: {e}\n\nTraceback: {traceback.format_exc()}'
        )

    if refund_payment:
        await bot.refund_star_payment(
            user_id=message.from_user.id,
            telegram_payment_charge_id=message.successful_payment.telegram_payment_charge_id,
        )
