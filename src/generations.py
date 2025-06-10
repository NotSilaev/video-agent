from logs import addLog
from database.tables.generations import addGeneration, getScheduledGenerations, getOrderGenerations
from telegram.api import sendRequest as sendTelegramAPIRequest
from permissions import getPermissionLevelUsers

from orders import makeOrderStructure

import datetime
import json


def makeGenerationsSchedule(total_videos: int, videos_peer_week: int) -> list[dict]:
    "Distributes the generation evenly over the weeks."

    today = datetime.date.today()
    
    # Start generation since the next day
    start_date = today + datetime.timedelta(days=1)
    
    generations_schedule = []
    videos_remaining = total_videos
    time_slots = ['morning', 'evening']
    
    while videos_remaining > 0:
        # Determine how many videos to generation this week
        videos_this_week = min(videos_peer_week, videos_remaining)
        
        # Distribute the publication days evenly throughout the week
        days_to_generation = sorted({(i * 7 // videos_this_week) % 7 for i in range(videos_this_week)})
        
        for day_offset in days_to_generation:
            # Choose time slot (alternate morning/evening)
            generation_time_slot = time_slots[len(generations_schedule) % 2]
            
            generation_date = (start_date + datetime.timedelta(days=day_offset))
            generation_data = {
                'date': generation_date,
                'time_slot': generation_time_slot
            }
            generations_schedule.append(generation_data)
            
            videos_remaining -= 1
            if videos_remaining == 0:
                break
        
        # Transfer to the next week
        start_date += datetime.timedelta(weeks=1)

    return generations_schedule[:total_videos]


def getGenerationsScheduleData(generations: list) -> dict:
    generations_dates = []
    completed_generations_count = 0

    for generation in generations:
        date = generation['date']
        date = datetime.datetime.strftime(date, '%d-%m-%Y')

        time_slot = generation['time_slot']
        match time_slot:
            case 'morning': time_slot = 'Утро'
            case 'evening': time_slot = 'Вечер'

        is_completed = generation['is_completed']
        if is_completed: 
            emoji_status = '✅'
            completed_generations_count += 1
        else: 
            emoji_status = '⏳'

        generations_dates.append(
            f'— {emoji_status} {date} ({time_slot})'
        )

    generations_dates_list = '\n'.join(generations_dates)

    generations_schedule_data = {
        'dates_list': generations_dates_list,
        'completed_generations_count': completed_generations_count
    }

    return generations_schedule_data


def sendGenerationsSheduleToCleint(user_id: int, order_id: str) -> None:
    short_order_id = order_id.split('-')[0]

    generations: list = getOrderGenerations(order_id)
    generations_schedule_data: dict = getGenerationsScheduleData(generations)
    generations_dates_list: str = generations_schedule_data['dates_list']

    message_text = (
        f'📅 График публикаций сформирован для заказа {short_order_id} \n\n'
        f'{generations_dates_list}'
    )

    keyboard = json.dumps({
        "inline_keyboard": [ # Keyboard
            [
                {
                    "text": "🎬 Открыть заказ",
                    "callback_data": f"order_card-{order_id}"
                },
            ],
        ]
    })

    sendTelegramAPIRequest(
        request_method='POST',
        api_method='sendMessage',
        parameters={
            'chat_id': user_id,
            'text': message_text,
            'reply_markup': keyboard,
        },
    )

def scheduleGenerations(user_id: int, order_id: str, order_data: dict) -> None:
    count = order_data['count']
    periodicity = order_data['periodicity']

    generations_schedule: list = makeGenerationsSchedule(total_videos=count, videos_peer_week=periodicity)

    for generation_data in generations_schedule:
        addGeneration(order_id, generation_data)
    
    sendGenerationsSheduleToCleint(user_id, order_id)


def sendGenerationNotificationsToAdmins(generation: dict) -> None:
    generation_id = generation['id']
    order_data = generation['order_data']
    generation_admin = generation['admin_id']

    if generation_admin:
        return

    order_structure = makeOrderStructure(order_data)

    admins = getPermissionLevelUsers(level='admin')
    for admin_user_id in admins:
        message_text = (
            f'*🔔 Запланирована генерация видео*\n\n'
            f'{order_structure}'
        )

        keyboard = json.dumps({
            "inline_keyboard": [
                [
                    {
                        "text": "📥 Принять генерацию в работу",
                        "callback_data": f"take_generation-{generation_id}"
                    },
                ],
            ]
        })

        sendTelegramAPIRequest(
            request_method='POST',
            api_method='sendMessage',
            parameters={
                'chat_id': admin_user_id,
                'text': message_text,
                'parse_mode': 'Markdown',
                'reply_markup': keyboard,
            },
        )  

def processGenerations(time_slot: str) -> None:
    date = datetime.date.today()

    generations: list = getScheduledGenerations(date, time_slot)

    for generation in generations:
        sendGenerationNotificationsToAdmins(generation)
