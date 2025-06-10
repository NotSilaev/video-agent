import sys
sys.path.append('../../') # src/

from bot.exceptions import exceptions_catcher
from bot.utils import respondEvent

from database.tables.generations import getGeneration, updateGenerationAdmin
from permissions import check_permissions

from orders import makeOrderStructure

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext

import datetime


router = Router(name=__name__)


@router.callback_query(F.data.startswith('take_generation'))
@check_permissions(level='admin')
@exceptions_catcher()
async def take_generation(call: CallbackQuery) -> None:
    user_id = call.from_user.id
    generation_id = '-'.join(call.data.split('-')[1:])

    generation: dict = getGeneration(generation_id)

    generation_admin = generation['admin_id']
    if generation_admin:
        await respondEvent(call, text='❌ Данная генерация уже закреплена за другим администратором.')
        return

    updateGenerationAdmin(generation_id, user_id)

    message_text = '✅ Генерация закреплена за Вами.'

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='🎥 Начать работу', callback_data=f'start_generation-{generation_id}')

    await respondEvent(
        call,
        text=message_text,
        parse_mode="Markdown",
        reply_markup=keyboard.as_markup()
    )


@router.callback_query(F.data.startswith('start_generation'))
async def start_generation(call: CallbackQuery) -> None:
    generation_id = '-'.join(call.data.split('-')[1:])
    
    