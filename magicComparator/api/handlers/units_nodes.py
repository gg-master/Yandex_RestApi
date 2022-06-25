from http import HTTPStatus
from typing import Dict

from aiohttp.web_response import Response
from aiohttp_apispec import docs, response_schema

from magicComparator.api.schema import ShopUnitNodesResponseSchema
from magicComparator.db.schema import ShopUnitType
from .base import BaseUnitView
from .queries import NOT_UPDATED_CATEGORIES_CHILDREN_Q, \
    NUP_OFFERS_CHILD_Q, AVG_PRICE_Q, \
    OFFERS_Q, CATEGORY_Q


class NodesUnitView(BaseUnitView):
    URL_PATH = r'/nodes/{id}'

    async def config_category(self, category, children_buf) -> Dict:
        """
        Добавляет в переданную категорию ее детей-товаров и вложенные категории
        :param category: Категория, к которой нужно добавить детей
        :param children_buf: Буффер с вычесленными ранее категориями
        :return: category с детьми
        """
        cid = category['id']

        # Добавляем товары категории
        category['children'].extend(map(
            dict, await self.pg.query(NUP_OFFERS_CHILD_Q.format(cid))
        ))

        # Добавляем вложенные категории
        category['children'].extend(children_buf.get(cid, []))
        return category

    async def config_children4head(self, head_category):
        """
        Конфигурирует дерево для искомой категории
        :param head_category: Категория, по которой составляется статистика
        """
        # Получение всех вложенных категорий в упорядоченном формате
        categories = await self.pg.query(
            NOT_UPDATED_CATEGORIES_CHILDREN_Q.format(head_category['id']))

        # Временный буфер для хранения вложенных детей
        children = {}  # {parent_id: [child1, child2]}

        # Начинаем формировать дерева с конца
        for i in range(len(categories) - 1, -1, -1):
            # Конфигурируем данные категории-ребенка
            pre_res = {i: k for i, k in categories[i].items()}

            # Высчитываем среднюю цену для категории
            pre_res['price'] = await self.pg.fetchval(
                AVG_PRICE_Q.format(pre_res['id']))

            pre_res['children'] = []

            # Добавляем детей-товаров для категории
            await self.config_category(pre_res, children)

            # Добавляем сконфигурированную категорию в буфер
            if pre_res['parentId'] not in children:
                children[pre_res['parentId']] = [pre_res.copy()]
            else:
                children[pre_res['parentId']].append(pre_res.copy())

        await self.config_category(head_category, children)

    @classmethod
    async def get_offers_nodes(cls, conn, uid: str) -> Dict:
        """
        Возвращает статистику по товару
        :param conn: SAConnection to db
        :param uid: offer uuid
        :return: Dictionary with offer params
        """
        return dict(await conn.fetchrow(OFFERS_Q.format(uid)))

    async def get_category_nodes(self, uid: str) -> Dict:
        # Получение информации о искомой категории
        curr_category = await self.pg.query(CATEGORY_Q.format(uid))

        # Конфигурируем выходное дерево
        data = {i: k for i, k in curr_category[0].items()}
        data['price'] = await self.pg.fetchval(AVG_PRICE_Q.format(uid))
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

    @docs(summary='Получить информацию о юните по его id.')
    @response_schema(ShopUnitNodesResponseSchema(), code=HTTPStatus.OK.value)
    async def get(self):
        async with self.pg.transaction() as conn:
            # Получение юнита и всех его вложенных детей
            body = await self.get_unit_nodes(conn, self.unit_id)

        return Response(body=body, status=HTTPStatus.OK)
