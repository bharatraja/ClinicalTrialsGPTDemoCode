import asyncpg
import asyncio
from aiohttp.web_app import Application
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from asyncpg.pool import Pool
import os


DB_KEY = 'database'

#method to acquire connection
def getConnection(request:Request):
    return request.app[DB_KEY]


async def create_database_pool(app: Application):          
    print('Creating database pool.')
    db_password = os.environ.get('SYNTHEA_DB_PASSWORD')
    db_user = os.environ.get('SYNTHEA_DB_USER')
    db_host = os.environ.get('SYNTHEA_DB_HOST')
    db_port = os.environ.get('SYNTHEA_DB_PORT')
    db_pool_min_size = os.environ.get('SYNTHEA_DB_POOL_MIN_SIZE')
    db_pool_max_size = os.environ.get('SYNTHEA_DB_POOL_MAX_SIZE')
    db_database=os.environ.get('SYNTHEA_DB_NAME')

    print(db_password,db_user,db_host,db_port,db_pool_min_size,db_pool_max_size,db_database)

    pool: Pool = await asyncpg.create_pool(host=db_host,
                                           port=int(db_port),
                                           user=db_user,
                                           password=db_password,
                                           database=db_database,
                                           min_size=int(db_pool_min_size),
                                           max_size=int(db_pool_max_size))

    app[DB_KEY] = pool


async def destroy_database_pool(app: Application):         
    print('Destroying database pool.')
    pool: Pool = app[DB_KEY]
    await pool.close()
