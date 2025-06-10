import sys
sys.path.append('../') # src/

from config import settings

import psycopg2


def getDatabaseConnection() -> psycopg2.extensions.connection:
    return psycopg2.connect(
        host=settings.db_host, 
        port=settings.db_port,
        dbname=settings.db_name, 
        user=settings.db_user,
        password=settings.db_password, 
    )


def execute(stmt: str, params: tuple) -> None:
    with getDatabaseConnection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(stmt, params)


def fetch(query: str, params: tuple, fetch_type: str, as_dict: bool = False) -> list:
    '''Executes an SQL fetch query.
    
    :param query: SQL fetch query.
    :param fetch_type: if `one`, the fetchone() function will be executed, if `all` - the fetchall().
    :param as_dict: if `True`, returns the response in the dictionary view (works only with `all` fetch_type).
    '''

    with getDatabaseConnection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params)

            match fetch_type:
                case 'one': response = cursor.fetchone()
                case 'all': response = cursor.fetchall()
                case _:
                    raise ValueError('Invalid fetch_type')

    if as_dict:
        columns = [desk[0] for desk in cursor.description]
        match fetch_type:
            case 'all':
                response = [dict(zip(columns, row)) for row in response]
            case 'one':
                response = dict(zip(columns, response))

    return response
