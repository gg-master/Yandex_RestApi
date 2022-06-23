from datetime import datetime
from http import HTTPStatus
from typing import Dict

from aiohttp.web_response import Response
from aiohttp_apispec import docs, response_schema, request_schema

from magicComparator.api.schema import ShopUnitStatSchema, \
    ShopUnitStatResponseSchema, DATETIME_FORMAT
from magicComparator.db.schema import ShopUnitType
from magicComparator.utils.pg import SelectQuery
from .base import BaseUnitView
from .queries import AVG_PRICE_BY_DATE, CATEGORY_STAT_Q, OFFER_STAT_Q


class UnitStatView(BaseUnitView):
    URL_PATH = r'/node/{id}/statistic'

    async def get_category_stat(self, uid, date_start, date_end) -> Dict:
        # Получаем все записи категории, лежащих в диапазоне дат
        category_hist = await self.pg.query(CATEGORY_STAT_Q.format(
            uid=uid, date_start=date_start, date_end=date_end))

        items = []
        # Для каждого элемента высчитываем среднюю цену на тот моммент
        for category_item in category_hist:
            item = dict(category_item)
            item['price'] = await self.pg.fetchval(AVG_PRICE_BY_DATE.format(
                uid=uid, date_end=item['date']))
            items.append(item)

        return {'items': items}

    @docs(summary='Получить статистику обновления юнитов за указанный период.')
    @request_schema(ShopUnitStatSchema())
    @response_schema(ShopUnitStatResponseSchema(), code=HTTPStatus.OK)
    async def get(self):
        date_end: datetime = self.request['data'].get(
            'dateEnd', datetime.now())
        date_start: datetime = self.request['data'].get(
            'dateStart', datetime.strptime('0001-01-01T01:00:00.000Z',
                                           DATETIME_FORMAT))
        uid = self.unit_id

        u_type = await self.get_unit_type(self.pg, uid)
        body = {}
        if u_type.upper() == ShopUnitType.offer.value:
            body = SelectQuery(OFFER_STAT_Q.format(
                uid=uid, date_start=date_start, date_end=date_end),
                self.pg.transaction())

        elif u_type.upper() == ShopUnitType.category.value:
            body = await self.get_category_stat(uid, date_start, date_end)

        return Response(body=body, status=HTTPStatus.OK)
