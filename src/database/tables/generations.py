import sys
sys.path.append('../../') # src/

from database.main import execute, fetch

import uuid
import datetime


def addGeneration(order_id: str, generation_data: dict[datetime.date, str]) -> str:
    generation_id = str(uuid.uuid4())
    date = generation_data['date']
    time_slot = generation_data['time_slot']

    stmt = '''
        INSERT INTO generations
        (id, order_id, date, time_slot)
        VALUES (%s, %s, %s, %s)
    '''
    params = (generation_id, order_id, date, time_slot)

    execute(stmt, params)

    return generation_id


def getGeneration(generation_id: str) -> dict:
    query = '''
        SELECT order_id, date, time_slot, is_completed, generated_video_id, admin_id
        FROM generations
        WHERE id = %s
    '''
    params = (generation_id, )
    
    generation: dict = fetch(query, params, fetch_type='one', as_dict=True)

    return generation


def getScheduledGenerations(date: datetime.date, time_slot: str) -> list:
    query = '''
        SELECT 
            g.id, 
            g.admin_id,
            g.is_completed,
            g.order_id,
            o.data AS order_data
        FROM generations g
        JOIN orders o
            ON g.order_id = o.id
        WHERE 
            g.date = %s
            AND g.time_slot = %s
            AND g.is_completed = %s
    '''
    params = (date, time_slot, False)
    
    generations: list = fetch(query, params, fetch_type='all', as_dict=True)

    return generations


def getOrderGenerations(order_id: str) -> list:
    query = '''
        SELECT date, time_slot, is_completed, generated_video_id
        FROM generations
        WHERE order_id = %s
    '''
    params = (order_id, )

    generations: list = fetch(query, params, fetch_type='all', as_dict=True)

    return generations


def updateGenerationAdmin(generation_id: str, admin_id: int) -> None:
    stmt = '''
        UPDATE generations
        SET admin_id = %s
        WHERE id = %s
    '''
    params = (admin_id, generation_id)
    execute(stmt, params)
