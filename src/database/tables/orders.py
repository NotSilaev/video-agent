import sys
sys.path.append('../../') # src/

from database.main import execute, fetch

import uuid
import json
import datetime


def addOrder(user_id: int, order_data: dict) -> str:
    order_id = str(uuid.uuid4())
    order_data_json = json.dumps(order_data)
    created_at = datetime.datetime.now()

    stmt = '''
        INSERT INTO orders
        (id, user_id, data, created_at)
        VALUES (%s, %s, %s, %s)
    '''
    params = (order_id, user_id, order_data_json, created_at)

    execute(stmt, params)

    return order_id


def getOrder(order_id: str) -> dict | None:
    query = '''
        SELECT user_id, data, created_at
        FROM orders
        WHERE id = %s
    '''
    params = (order_id, )

    order: dict | None = fetch(query, params, fetch_type='one', as_dict=True)

    return order


def getUserOrders(user_id: int, period: tuple = None, is_completed: bool = None) -> list:
    params = []

    params.append(user_id)

    period_condition = ''
    if period is not None:
        start_date, end_date = period
        period_condition = '(o.created_at BETWEEN %s AND %s)'
        params.append(start_date, end_date)
    
    is_completed_condition = ''
    if is_completed is not None:
        if is_completed is True:
            is_completed_condition = """
                GROUP BY o.id, o.created_at
                HAVING NOT EXISTS (
                    SELECT 1 FROM generations g2 
                    WHERE g2.order_id = o.id AND g2.is_completed = FALSE
                )
            """
        elif is_completed is False:
            is_completed_condition = """
                GROUP BY o.id, o.created_at
                HAVING EXISTS (
                    SELECT 1 FROM generations g2
                    WHERE g2.order_id = o.id AND g2.is_completed = FALSE
                )
            """

    params = tuple(params)

    query = f'''
        SELECT o.id, o.data, o.created_at
        FROM orders o
        JOIN generations g
        ON g.order_id = o.id
        WHERE 
            user_id = %s
            {period_condition}
        {is_completed_condition}
        ORDER BY o.created_at
    '''
    
    orders: list = fetch(query, params, fetch_type='all', as_dict=True)

    return orders
