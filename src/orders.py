from logs import addLog
from database.tables.orders import addOrder

import datetime
import traceback


def makeOrderStructure(order_data) -> str:
    structure_items = []
    for key, value in order_data.items():
        match key:
            case 'topic': structure_items.append(f'🚀 Тематика: {value}')
            case 'style': structure_items.append(f'👨‍🎨 Стиль: {value}')
            case 'count': structure_items.append(f'📼 Количество: {value}')
            case 'platforms': 
                platforms = ", ".join(value) if value else "не выбраны"
                structure_items.append(f'📲 Платформы: {platforms}')
            case 'periodicity': structure_items.append(f'📅 Периодичность: {value} видео в неделю')
            case 'watermark': 
                watermark_status = "добавлен" if value else "не добавлен"
                structure_items.append(f'🪧 Водяной знак: {watermark_status}')
            case 'publication_method': 
                match value:
                    case 'auto': publication_method = 'автоматический'
                    case 'manual': publication_method = 'ручной'
                    case 'independent': publication_method = 'самостоятельный'
                    case _: publication_method = 'не выбран'
                structure_items.append(f'📤 Способ публикации: {publication_method}')
            case 'publication_account': 
                match value:
                    case 'client': publication_account = 'клиентский'
                    case 'service': publication_account = 'сервисный'
                    case _: publication_account = 'не выбран'
                structure_items.append(f'📺 Аккаунт публикации: {publication_account}')
            case 'price': structure_items.append(f'💰 Стоимость заказа: {value} 🌟')

    structure_items_string = '\n'.join(structure_items)

    order_structure = (
        '——— Состав заказа ———\n'
        f'{structure_items_string}\n'
        '—————————————'
    )

    return order_structure


def processOrder(user_id: int, order_data: dict) -> None:
    order_id = addOrder(user_id, order_data)

    from generations import scheduleGenerations
    scheduleGenerations(user_id, order_id, order_data)
