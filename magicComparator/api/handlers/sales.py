from datetime import timedelta, datetime
from http import HTTPStatus

from aiohttp.web_response import Response
from aiohttp_apispec import docs, response_schema, request_schema

from magicComparator.api.schema import ShopUnitsSalesSchema, \
    ShopUnitSalesResponseSchema
from magicComparator.utils.pg import SelectQuery
from .base import BaseUnitView
from .queries import OFFERS_SALES_Q


class SalesOffersView(BaseUnitView):
    URL_PATH = r'/sales'

    @docs(summary='Получить все обновленные товары за сутки.')
    @request_schema(ShopUnitsSalesSchema())
    @response_schema(ShopUnitSalesResponseSchema(), code=HTTPStatus.OK)
    async def get(self):
        date_end: datetime = self.request['data']['date']
        date_start: datetime = date_end - timedelta(days=1)

        query = OFFERS_SALES_Q.format(date_start=date_start,
                                      date_end=date_end)
        body = SelectQuery(query, self.pg.transaction())

        return Response(body=body, status=HTTPStatus.OK)
