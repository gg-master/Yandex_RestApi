from aiohttp.web_exceptions import HTTPNotFound
from aiohttp.web_urldispatcher import View
from asyncpgsa import PG
from sqlalchemy import exists, select, or_

from magicComparator.db.schema import offers_table, category_table


class BaseView(View):
    URL_PATH: str

    @property
    def pg(self) -> PG:
        return self.request.app['pg']


class BaseUnitView(BaseView):
    @property
    def unit_id(self):
        return str(self.request.match_info.get('id'))

    async def check_unit_exists(self, uid):
        query = select([
            exists().where(or_(
                offers_table.c.id == uid,
                category_table.c.id == uid))
        ])
        if not await self.pg.fetchval(query):
            raise HTTPNotFound()

    @classmethod
    async def get_unit_type(cls, conn, uid: str) -> str:
        q = f'''
               SELECT 'CATEGORY' as type FROM category
               WHERE category.id = '{uid}'
               UNION SELECT 'OFFER' as type FROM offers
               WHERE offers.id = '{uid}'
           '''

        unit_type = await conn.fetchval(q)
        if not unit_type:
            raise HTTPNotFound()
        return unit_type
