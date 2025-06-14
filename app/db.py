import asyncio
import aiosqlite
import os
from quart import g, current_app

def init_app(app):
    # закрытие соединения при teardown
    @app.teardown_appcontext
    def close_db(exc):
        db = g.pop('db', None)
        if db:
            asyncio.run(db.close())

async def _init_db(db_path):
    async with aiosqlite.connect(db_path) as db:
        # читаем и выполняем schema.sql
        here = os.path.dirname(__file__)
        with open(os.path.join(here, '../schema.sql'), 'r') as f:
            await db.executescript(f.read())
        await db.commit()

async def get_db():
    if 'db' not in g:
        g.db = await aiosqlite.connect(
            current_app.config['DATABASE']
        )
        g.db.row_factory = aiosqlite.Row
    return g.db