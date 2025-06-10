import sys
sys.path.append('../../') # src/

from logs import addLog

from bot.exceptions import exceptions_catcher
from bot.utils import respondEvent

from permissions import check_permissions

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext


router = Router(name=__name__)


@router.callback_query(F.data == 'admin')
@check_permissions(level='admin')
@exceptions_catcher()
async def admin_menu(call: CallbackQuery) -> None:
    ...
