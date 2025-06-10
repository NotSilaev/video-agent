import sys
sys.path.append('../') # src/

from config import settings

import requests


def sendRequest(request_method: str, api_method: str, parameters:dict={}) -> str:
    '''Sends request to Telegram API.

    :param request_method: http request method (`get` or `post`).
    :param api_method: the required method in Telegram API.
    :param parameters: dict of parameters which will used in the Telegram API method.
    '''

    token = settings.telegram_bot_token
    request = f"https://api.telegram.org/bot{token}/{api_method}?{'&'.join([f'{k}={v}' for k, v in parameters.items()])}"

    if request_method == 'GET':
        r = requests.get(request)
    elif request_method == 'POST':
        r = requests.post(request)

    response = {
        'code': r.status_code,
        'text': r.text,
    }
    
    return response
