from http import HTTPStatus

from typing import Dict

from aiohttp.web_exceptions import HTTPNotFound
from aiohttp.web_response import Response
from aiohttp_apispec import docs, response_schema
from sqlalchemy import select, and_

from magicComparator.api.schema import ShopUnitNodesResponseSchema
from magicComparator.db.schema import offers_table, category_table, \
    ShopUnitType

from .base import BaseUnitView
from .queries import NOT_UPDATED_CATEGORIES_CHILDREN_Q, \
    NOT_UPDATED_OFFERS_CHILDREN_Q, OFFERS_QUERY, CATEGORY_QUERY, AVG_PRICE_Q


class NodesUnitView(BaseUnitView):
    URL_PATH = r'/nodes/{id}'

    async def config_category(self, category, children_buf):
        cid = category['id']

        # Добавляем товары категории
        category['children'].extend(
            map(lambda x: {
                'name': x['name'],
                'id': x['id'],
                'parentId': x['parent_id'],
                'date': x['date'],
                'price': x['price'],
                'type': x['type'].upper(),
                'children': None,
            },
                await self.pg.query(
                    NOT_UPDATED_OFFERS_CHILDREN_Q.format(f"('{cid}')")
                ))
        )

        # Добавляем вложенные категории
        category['children'].extend(children_buf.get(cid, []))
        return category

    async def config_children4head(self, data):
        # Получение всех вложенных категорий
        categories = await self.pg.query(
            NOT_UPDATED_CATEGORIES_CHILDREN_Q.format(data['id']))

        # Временный буфер для хранения вложенных детей
        children = {}  # {parent_id: [child1, child2]}

        # Начинаем формировать дерева с конца
        for i in range(len(categories) - 1, -1, -1):
            # Конфигурируем данные категории-ребенка
            pre_res = {i: k for i, k in categories[i].items()}
            pre_res['type'] = data['type'].upper()
            parent_id = pre_res['parentId'] = pre_res.pop('parent_id')

            pre_res['price'] = await self.pg.fetchval(
                AVG_PRICE_Q.format(pre_res['id']))
            pre_res['price'] = int(pre_res['price']) if pre_res['price'] else 0

            pre_res['children'] = []

            # Добавляем детей-товаров для категории
            await self.config_category(pre_res, children)

            if parent_id not in children:
                children[parent_id] = [pre_res.copy()]
            else:
                children[parent_id].append(pre_res.copy())

        await self.config_category(data, children)

    @classmethod
    async def get_unit_type(cls, conn, uid: str) -> str:
        q = select([category_table.c.type]).where(
            category_table.c.id == uid).union(
            select([offers_table.c.type]).where(offers_table.c.id == uid))

        unit_type = await conn.fetchval(q)
        if not unit_type:
            raise HTTPNotFound()
        return unit_type

    @classmethod
    async def get_offers_nodes(cls, conn, uid: str) -> Dict:
        # Если тип юнита - товар, то просто возвращаем сразу все поля
        q = OFFERS_QUERY.where(and_(offers_table.c.id == uid,
                                    offers_table.c.updated == False))
        res = await conn.fetchrow(q)

        # Конфигурируем словарь для ответа
        data = {i: k for i, k in res.items()}
        data['type'] = data['type'].upper()
        data['parentId'] = next(iter(data.pop('parent_id')), None)

        return data

    async def get_category_nodes(self, uid: str) -> Dict:
        # Получение информации о искомой категории
        curr_category = await self.pg.query(CATEGORY_QUERY.where(and_(
            category_table.c.id == uid, category_table.c.updated == False)))

        # Конфигурируем выходное дерево
        data = {i: k for i, k in curr_category[0].items()}
        data['type'] = data['type'].upper()
        data['parentId'] = next(iter(data.pop('parent_id')), None)

        data['price'] = await self.pg.fetchval(AVG_PRICE_Q.format(uid))
        data['price'] = int(data['price']) if data['price'] else 0

        data['children'] = []

        # # Добавляем детей для искомого объекта
        await self.config_children4head(data)

        return data

    async def get_unit_nodes(self, conn, uid) -> Dict:
        """
        Получение информации о юните
        :param conn: Транзакция с базой
        :param uid: Id юнита
        :return: Dict - словарь с информацией о юните
        """
        u_type = await self.get_unit_type(conn, uid)

        if u_type.upper() == ShopUnitType.offer.value:
            return await self.get_offers_nodes(conn, uid)

        elif u_type.upper() == ShopUnitType.category.value:
            return await self.get_category_nodes(uid)

    @docs(summary='Удалить всю информацию юнита')
    @response_schema(ShopUnitNodesResponseSchema(), code=HTTPStatus.OK)
    async def get(self):
        async with self.pg.transaction() as conn:
            # Получение юнита и всех его вложенных детей
            body = await self.get_unit_nodes(conn, self.unit_id)

        return Response(body=body, status=HTTPStatus.OK)
