import sys
sys.path.append('../') # src/

from logs import addLog
from telegram.api import sendRequest as sendTelegramAPIRequest

import traceback
import functools


def exceptions_catcher(): 
    """Catches all the exceptions in functions.
    If exception is noticed, it adds a new note to a logfile 
    and sends a telegram message for user about unsuccessful request.
    """

    def container(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                user_id = args[0].from_user.id
            except (IndexError, AttributeError):
                user_id = None

            try:
                result = await func(*args, **kwargs)
            except Exception as e:
                log_text = f'{e}\n\n{traceback.format_exc()}'
                addLog(level='error', text=log_text)

                if user_id:
                    message_text = (
                        '*❌ Во время исполнения Вашего запроса произошла неизвестная ошибка.*\n\n'
                        'Попробуйте повторить свой запрос, если ничего не изменится - подождите некоторое время.\n\n'
                        '*🙏 Приносим свои извенения за предоставленные неудобства.*'
                    )

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
