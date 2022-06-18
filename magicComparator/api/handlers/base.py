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
