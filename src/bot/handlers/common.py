import sys
sys.path.append('../../') # src/

from logs import addLog

from generations import processGenerations # remove it later

from bot.exceptions import exceptions_catcher
from bot.utils import (
    respondEvent, 
    deserializeEvent, 
    normalizeJSONStringValues, 
    makeGreetingMessage, 
    getUserName
)

from permissions import hasUserPermission

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext


router = Router(name=__name__)


@router.message(Command('proc'))
async def proc(event: Message) -> None:
    processGenerations('evening')


@router.message(CommandStart())
@router.callback_query(F.data == 'start')
@router.message(F.text & (~F.text.startswith("/")), StateFilter(None))
@exceptions_catcher()
async def start(event: Message | CallbackQuery, state: FSMContext) -> None:
    if isinstance(event, Message):
        user_id = event.from_user.id
    elif isinstance(event, CallbackQuery):
        user_id = event.message.from_user.id

    await state.clear()

    greeting: str = makeGreetingMessage()
    user_name: str = getUserName(user=event.from_user)

    description = '*Video Agent* — система автоматизированной генерации и публикации вертикальных видео для платформ: YouTube Shorts, Instagram Reels, TikTok.'

    message_text = (
        f'*{greeting}*, {user_name}\n\n'
        f'{description}'
    )

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='🎬 Создать заказ', callback_data='create_order')
    keyboard.button(text='🗂 Мои заказы', callback_data='orders')
    keyboard.button(text='📈 Статистика', callback_data='stats')
    keyboard.button(text='ℹ️ О сервисе', callback_data='info')
    keyboard.button(text='💬 Поддержка', callback_data='support')

    if hasUserPermission(user_id, level='admin'):
        keyboard.button(text='👨🏼‍💻 Админ-меню', callback_data='admin')

    keyboard.adjust(1, 2, 1)

    await respondEvent(
        event,
        text=message_text, 
        parse_mode="Markdown", 
        reply_markup=keyboard.as_markup()
    )
