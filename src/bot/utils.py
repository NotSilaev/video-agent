from aiogram import Bot
from aiogram.types import Message, CallbackQuery
from aiogram.types.user import User

import json
import datetime


async def respondEvent(event: Message | CallbackQuery, **kwargs):
    "Responds to various types of events: messages and callback queries"

    if isinstance(event, Message):
        await event.answer(**kwargs)
    elif isinstance(event, CallbackQuery):
        await event.message.edit_text(**kwargs)
        await event.answer()


def serializeEvent(event: Message | CallbackQuery) -> str:
    if isinstance(event, Message): 
        event_type = 'message'
    elif isinstance(event, CallbackQuery): 
        event_type = 'callbackquery'

    event_dict: dict = event.model_dump()
    event_dict['type'] = event_type
    event_json = json.dumps(event_dict)

    return event_json


def deserializeEvent(event_json: str | dict) -> Message | CallbackQuery:
    if isinstance(event_json, str):
        event_json: dict = json.loads(event_json)

    event_type = event_json['type']
    del event_json['type']

    match event_type:
        case 'message':
            event = Message.model_validate(event_json)
        case 'callbackquery':
            event = CallbackQuery.model_validate(event_json)

    return event


def normalizeJSONStringValues(json_string: str) -> str:
    "Converts values in a string to Python format."

    return (
        json_string
           .replace('null', 'None')
           .replace('true', 'True')
           .replace('false', 'False')
    )
    

def makeGreetingMessage() -> str:
    '''Generates a welcome message based on the current time of day.'''

    hour = datetime.datetime.now().hour

    if hour in range(0, 3+1) or hour in range(22, 23+1): # 22:00 - 3:00 is night
        greeting = '🌙 Доброй ночи'
    elif hour in range(4, 11+1): # 4:00 - 11:00 is morning
        greeting = '☕️ Доброе утро'
    elif hour in range(12, 17+1): # 12:00 - 17:00 is afternoon
        greeting = '☀️ Добрый день'
    elif hour in range(18, 21+1): # 18:00 - 21:00 is evening
        greeting = '🌆 Добрый вечер'
    else:
        greeting = '👋 Доброго времени суток'
    
    return greeting


def getUserName(user: User) -> str:
    '''Generates a string to address the user.
    
    :param user: the user's aiogram object.
    '''

    user_id: int = user.id
    username: str = user.username
    first_name: str = user.first_name
    last_name: str = user.last_name
    
    if first_name:
        if last_name:
            user_name = f'{first_name} {last_name}'
        else:
            user_name = first_name
    elif username:
        user_name = f'@{username}'
    else:
        user_name = f'пользователь №{user_id}'

    return user_name


def makeCleanTimestamp(timestamp: datetime.datetime) -> str:
    '''Translates datetime into a string of a form: "yyyy-mm-dd HH:MM".'''
    
    return f"{timestamp.strftime('%Y-%m-%d %H:%M')}"
