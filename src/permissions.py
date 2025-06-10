from config import settings
from logs import addLog
from telegram.api import sendRequest as sendTelegramAPIRequest

import traceback
import functools
from textwrap import dedent


def getPermissionLevelUsers(level: str) -> list:
    permission_levels = {
        'admin': settings.admin_list,
    }
    return permission_levels[level]


def hasUserPermission(user_id: int, level: str) -> bool:
    permission_level_users: list = getPermissionLevelUsers(level)
    if user_id in permission_level_users:
        return True
    return False


def check_permissions(level: str): 
    "Сhecks whether the user has access rights to the handler."

    def container(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                user_id = args[0].from_user.id
            except (IndexError, AttributeError):
                user_id = None

            if hasUserPermission(user_id, level):
                result = await func(*args, **kwargs)
            else:
                message_text = '🚫 У Вас нет доступа к данному разделу.'

                sendTelegramAPIRequest(
                    request_method='POST',
                    api_method='sendMessage',
                    parameters={
                        'chat_id': user_id,
                        'text': message_text,
                        'parse_mode': 'Markdown',
                    },
                )

        return wrapper
    return container
