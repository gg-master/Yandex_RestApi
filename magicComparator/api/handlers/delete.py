from http import HTTPStatus

from aiohttp.web_exceptions import HTTPNotFound
from aiohttp.web_response import Response
from aiohttp_apispec import docs, response_schema
from sqlalchemy import select, or_

from magicComparator.api.schema import DeleteUnitResponseSchema
from magicComparator.db.schema import offers_table, category_table, \
    category_parents_table, offers_parents_table, ShopUnitType
from .base import BaseUnitView
from .queries import ALL_CATEGORIES_CHILDREN_Q, ALL_OFFERS_CHILDREN_Q


class DeleteUnitView(BaseUnitView):
    URL_PATH = r'/delete/{id}'

    @classmethod
    async def get_unit_type(cls, conn, uid):
        q = select([category_table.c.type]).where(
            category_table.c.id == uid).union(
            select([offers_table.c.type]).where(offers_table.c.id == uid))

        unit_type = await conn.fetchval(q)
        if not unit_type:
            raise HTTPNotFound()
        return unit_type

    @classmethod
    async def remove_offer(cls, conn, uid):
        # Если тип юнита - товар, то сначала удаляем все взаимосвязи с ним
        q = offers_parents_table.delete().where(
            offers_parents_table.c.child_id == uid)
        await conn.execute(q)

        # А потом все записи из общей базы
        q = offers_table.delete().where(offers_table.c.id == uid)
        await conn.execute(q)

    async def remove_category(self, conn, uid):
        # Получение всех вложенных категорий
        all_children_categories = await self.pg.query(
            ALL_CATEGORIES_CHILDREN_Q.format(uid))
        # Формируем множество уникальных id категорий
        all_categories_ids = set(
            i.get('id') for i in all_children_categories).union([uid])

        # Получение всех вложенных товаров
        all_children_offers = await self.pg.query(
            ALL_OFFERS_CHILDREN_Q.format(
                '(' + str(all_categories_ids)[1:-1] + ')'))
        # Формируем множество уникальных id товаров
        all_offers_ids = set(i.get('id') for i in all_children_offers)

        # Удаляем связи с детьми-товарами
        q = offers_parents_table.delete().where(or_(
            offers_parents_table.c.child_id.in_(all_offers_ids),
            offers_parents_table.c.parent_id.in_(all_categories_ids)
        ))
        await conn.execute(q)

        # Удаляем детей-товары
        q = offers_table.delete().where(
            offers_table.c.id.in_(all_offers_ids))
        await conn.execute(q)

        # Удаляем связи с детьми-категориями
        q = category_parents_table.delete().where(
            or_(
                category_parents_table.c.parent_id.in_(
                    all_categories_ids),
                category_parents_table.c.child_id.in_(
                    all_categories_ids)
            ))
        await conn.execute(q)

        q = category_table.delete().where(
            category_table.c.id.in_(all_categories_ids))
        await conn.execute(q)

    async def remove_unit_from_all(self, conn, uid):
        u_type = await self.get_unit_type(conn, uid)

        if u_type.upper() == ShopUnitType.offer.value:
            await self.remove_offer(conn, uid)

        elif u_type.upper() == ShopUnitType.category.value:
            await self.remove_category(conn, uid)

    @docs(summary='Удалить всю информацию юнита')
    @response_schema(DeleteUnitResponseSchema(), code=HTTPStatus.OK)
    async def delete(self):
        # Транзакция требуется чтобы в случае ошибки (или отключения клиента,
        # не дождавшегося ответа) откатить частично добавленные изменения.
        async with self.pg.transaction() as conn:
            # Удаление юнита и связанных с ним детей
            await self.remove_unit_from_all(conn, self.unit_id)

        return Response(status=HTTPStatus.OK)
