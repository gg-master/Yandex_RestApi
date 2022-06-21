from http import HTTPStatus
from typing import Generator

from asyncpg.exceptions import UniqueViolationError
from aiohttp.web_exceptions import HTTPNotFound, HTTPBadRequest
from aiohttp.web_response import Response
from aiohttp_apispec import docs, request_schema, response_schema
from aiomisc import chunk_list
from sqlalchemy import select, and_, exists

from magicComparator.api.schema import ShopUnitsImportSchema, \
    ShopUnitsImportResponseSchema
from magicComparator.db.schema import offers_table, category_table, \
    category_parents_table, offers_parents_table, ShopUnitType, updateDates, \
    unit_tables_association as utba, parent_tables_association as ptba
from magicComparator.utils.pg import MAX_QUERY_ARGS
from .base import BaseView
from .queries import CATEGORY_Q


class ImportsView(BaseView):
    URL_PATH = '/imports'
    # Так как данных может быть много, а postgres поддерживает только
    # MAX_QUERY_ARGS аргументов в одном запросе, писать в БД необходимо
    # частями.
    # Максимальное кол-во строк для вставки можно рассчитать как отношение
    # MAX_QUERY_ARGS к кол-ву вставляемых в таблицу столбцов.
    MAX_OFFERS_PER_INSERT = MAX_QUERY_ARGS // len(offers_table.columns)
    MAX_CATEGORY_PER_INSERT = MAX_QUERY_ARGS // len(category_table.columns)
    MAX_OF_PAR_PER_INSERT = MAX_QUERY_ARGS // len(offers_parents_table.columns)
    MAX_CA_PAR_PER_INSERT = MAX_QUERY_ARGS // len(
        category_parents_table.columns)

    @classmethod
    def make_shop_unit_rows(cls, items, date,
                            u_type: ShopUnitType) -> Generator:
        """
        Генерирует данные готовые для вставки в таблицы offer и category
        (без ключа parent_id).
        """
        for elem in items:
            if elem['type'] == u_type.value:
                data = {
                    'id': elem['id'],
                    'name': elem['name'],
                    'date': date,
                }
                if elem['type'] == ShopUnitType.offer.value:
                    data.update({'price': elem.get('price')})
                yield data

    @classmethod
    def make_parents_table_rows(cls, items, child_type, date) -> Generator:
        """
        Генерирует данные готовые для вставки в таблицы связей с родителями
        """
        for elem in items:
            if elem['type'] == child_type.value:
                if not elem.get('parentId'):
                    continue

                for parent_elem in items:
                    if elem['id'] != parent_elem['id'] and \
                            parent_elem['id'] == elem.get('parentId'):

                        # Проверка, что юниты имеют роидителей-категорий
                        if parent_elem['type'] != ShopUnitType.category.value:
                            raise HTTPBadRequest(
                                text=f'Родителем юнита {elem["id"]} '
                                     f'должна быть категория.')
                        yield {
                            'date': date,
                            'parent_id': parent_elem['id'],
                            'child_id': elem['id'],
                        }

    @classmethod
    async def update_parents(cls, conn, uid, parent_id, date, u_type):
        # Получаем данные родителя
        parent_unit = await conn.fetchrow(CATEGORY_Q.format(parent_id))

        # Если не нашли, то ошибку
        if not parent_unit:
            raise HTTPNotFound()

        # Если ранее для одного из товаров не создавали
        # обновленного родителя
        if not await conn.fetchval(select([exists().where(
                and_(category_table.c.date == date,
                     category_table.c.id == parent_id))])):
            q = category_table.insert().values({
                'date': date,
                'id': parent_id,
                'name': parent_unit['name'],
            })
            await conn.execute(q)

        if not await conn.fetchval(select([exists().where(
                and_(ptba[ShopUnitType[u_type]].c.date == date,
                     ptba[ShopUnitType[u_type]].c.child_id == uid))])):
            q = ptba[ShopUnitType[u_type]].insert().values(
                {'date': date, 'parent_id': parent_id, 'child_id': uid}
            )
            await conn.execute(q)
        # Возвращаем данные родителя, чтобы последовательно обновить всех
        return (
            parent_unit['id'],
            parent_unit['parentId'],
            parent_unit['type'].lower()
        )

    async def add_unit2existed_parent(self, conn, items, date):
        """
        Добавление новых юнитов к их уже существующим родителям.
        :param conn:
        :param items:
        :param date:
        :return:
        """
        for elem in items:
            uid, u_type = elem['id'], elem['type'].lower()
            parent_id = elem['parentId']

            # Добавлям актуальных родителей для юнита (обновляем их)
            while parent_id:
                uid, parent_id, u_type = await self.update_parents(
                    conn, uid, parent_id, date, u_type)

                # Добавляем новые элементы в список, чтобы впоследствии
                # пометить их родителей как обновленные
                items.append(
                    {'id': uid, 'type': u_type, 'parentId': parent_id})

    @classmethod
    async def mark_updated_old_units(cls, conn, items, date):
        """
        Отмечаем старые юниты как обновленные.
        Учитываем также и их родителя.
        :param conn:
        :param items:
        :param date:
        :return:
        """
        for elem in items:
            uid, u_type = elem['id'], elem['type'].lower()
            parent_id = elem['parentId']

            query = utba[ShopUnitType[u_type]].update() \
                .values({'updated': True}) \
                .where(and_(
                    utba[ShopUnitType[u_type]].c.id == uid,
                    utba[ShopUnitType[u_type]].c.date != date,
                    utba[ShopUnitType[u_type]].c.updated == False))
            await conn.execute(query)

            if parent_id:
                query = category_table.update() \
                    .values({'updated': True}) \
                    .where(and_(
                        category_table.c.id == parent_id,
                        category_table.c.date != date,
                        category_table.c.updated == False))
                await conn.execute(query)

    @docs(summary='Добавить / обновить информацию о товарах и категориях')
    @request_schema(ShopUnitsImportSchema())
    @response_schema(ShopUnitsImportResponseSchema(), code=HTTPStatus.OK)
    async def post(self):
        # Транзакция требуется чтобы в случае ошибки (или отключения клиента,
        # не дождавшегося ответа) откатить частично добавленные изменения.
        async with self.pg.transaction() as conn:
            items = self.request['data']['items']

            # Проверяем, что дата выгрузки уже не существует в базе
            try:
                query = updateDates.insert().values(
                    {'date': self.request['data']['updateDate']}) \
                    .returning(updateDates.c.date)
                date = await conn.fetchval(query)
            except UniqueViolationError:
                raise HTTPBadRequest(
                    text=f'updateDate {self.request["data"]["updateDate"]} '
                         f'уже существует.')

            offer_rows = self.make_shop_unit_rows(
                items, date, ShopUnitType.offer)
            category_rows = self.make_shop_unit_rows(
                items, date, ShopUnitType.category)

            offers_parents_rows = self.make_parents_table_rows(
                items, ShopUnitType.offer, date)
            category_parents_rows = self.make_parents_table_rows(
                items, ShopUnitType.category, date)

            # Чтобы уложиться в ограничение кол-ва аргументов в запросе к
            # postgres, а также сэкономить память и избежать создания полной
            # копии данных присланных клиентом во время подготовки - используем
            # генератор chunk_list.
            # Он будет получать из генераторов объем данных
            # необходимый для 1 запроса.
            chunked_offer_rows = chunk_list(offer_rows,
                                            self.MAX_OFFERS_PER_INSERT)
            chunked_category_rows = chunk_list(category_rows,
                                               self.MAX_CATEGORY_PER_INSERT)
            chunked_offer_par_rows = chunk_list(offers_parents_rows,
                                                self.MAX_OF_PAR_PER_INSERT)
            chunked_category_par_rows = chunk_list(category_parents_rows,
                                                   self.MAX_CA_PAR_PER_INSERT)

            query = offers_table.insert()
            for chunk in chunked_offer_rows:
                await conn.execute(query.values(list(chunk)))

            query = category_table.insert()
            for chunk in chunked_category_rows:
                await conn.execute(query.values(list(chunk)))

            query = offers_parents_table.insert()
            for chunk in chunked_offer_par_rows:
                await conn.execute(query.values(list(chunk)))

            query = category_parents_table.insert()
            for chunk in chunked_category_par_rows:
                await conn.execute(query.values(list(chunk)))

            # Добавляем недостающие связи с существующими элементами в бд
            await self.add_unit2existed_parent(conn, items, date)

            # Отмечаем все обновленные элементы
            await self.mark_updated_old_units(conn, items, date)

        return Response(status=HTTPStatus.OK)
