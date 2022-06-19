# import random
# import string
# from enum import EnumMeta
# from http import HTTPStatus
# from random import choice, randint, shuffle
# from typing import Any, Dict, Iterable, List, Mapping, Optional, Union
#
# import faker
# from aiohttp.test_utils import TestClient
# from aiohttp.typedefs import StrOrURL
# from aiohttp.web_urldispatcher import DynamicResource
# from magicComparator.api.schema import (
#     CitizenPresentsResponseSchema, CitizensResponseSchema,
#     ImportResponseSchema, PatchCitizenResponseSchema,
#     TownAgeStatResponseSchema,
# )
#
# from magicComparator.api.handlers import (
#     CitizenBirthdaysView, CitizensView, CitizenView, ImportsView,
#     TownAgeStatView,
# )
# from magicComparator.utils.pg import MAX_INTEGER
#
# fake = faker.Faker('ru_RU')
#
#
# def url_for(path: str, **kwargs) -> str:
#     """
#     Генерирует URL для динамического aiohttp маршрута с параметрами.
#     """
#     kwargs = {
#         key: str(value)  # Все значения должны быть str (для DynamicResource)
#         for key, value in kwargs.items()
#     }
#     return str(DynamicResource(path).url_for(**kwargs))
#
#
# def generate_unit(
#         uid: Optional[str] = None,
#         name: Optional[str] = None,
#         u_type: Optional[str] = None,
#         parent_id: Optional[str] = None,
#         price: Optional[int] = None,
# ) -> Dict[str, Any]:
#     """
#     Создает и возвращает Shop Unit, автоматически генерируя данные для не
#     указанных полей.
#     """
#     if uid is None:
#         uid = fake.unit_id()
#
#     if name is None:
#         name = fake.unit_name()
#
#     if u_type is None:
#         u_type = choice(('OFFER', 'CATEGORY'))
#
#     if price is None:
#         name = randint(0, MAX_INTEGER) if u_type == 'OFFER' else None
#
#     return {
#         'id': uid,
#         'name': name,
#         'type': u_type,
#         'parentId': parent_id,
#         'price': price,
#     }
#
#
# def generate_id():
#     letters = string.ascii_letters + string.digits
#     return f"{''.join(random.choice(letters) for i in range(8))}-" \
#            f"{''.join(random.choice(letters) for i in range(4))}-" \
#            f"{''.join(random.choice(letters) for i in range(4))}-" \
#            f"{''.join(random.choice(letters) for i in range(12))}"
#
#
# # def generate_units(
# #         categories_num: int = 5,
# #         offers_num: int = 5,
# #         nesting_depth: int = 1,
# #         **units_kwargs
# # ) -> List[Dict[str, Any]]:
# #     """
# #     Генерирует набор юнитов
# #     :param categories_num: Кол-во категорий
# #     :param offers_num: Кол-во товаров
# #     :param nesting_depth: Глубина вложенности. По умолчанию 1-вложенности нет.
# #     :param units_kwargs: Аргументы для функции generate_unit
# #     """
# #
# #     # Создаем категории
# #     categories = {}
# #     for i in range(categories_num):
# #         uid = generate_id()
# #
# #         if nesting_depth == 1:
# #             units_kwargs['parent_id'] = None
# #
# #         categories[uid] = generate_unit(uid=uid, **units_kwargs)
# #
# #     # Создаем товары
# #     offers = {}
# #     for i in range(offers_num):
# #         uid = generate_id()
# #         offers[uid] = generate_unit(uid=uid, **units_kwargs)
# #
# #     # Создаем вложенности
# #     categories_ids = list(categories.keys())
# #     offers_ids = list(offers.keys())
# #
# #     c_used_offers = c_used_categories = 0
# #     max_used_units = len(categories) + len(offers)
# #     while c_used_offers + c_used_categories < max_used_units:
# #
# #         for depth in range(nesting_depth):
# #
# #
# #     return list(citizens.values())
#
#
# def compare_units(left: Mapping, right: Mapping) -> bool:
#     return left == right
#
#
# async def import_data(
#         client: TestClient,
#         units: List[Mapping[str, Any]],
#         expected_status: Union[int, EnumMeta] = HTTPStatus.CREATED,
#         **request_kwargs
# ) -> Optional[int]:
#     response = await client.post(
#         ImportsView.URL_PATH, json={'citizens': citizens}, **request_kwargs
#     )
#     assert response.status == expected_status
#
#     if response.status == HTTPStatus.CREATED:
#         data = await response.json()
#         errors = ImportResponseSchema().validate(data)
#         assert errors == {}
#         return data['data']['import_id']
#
#
# async def get_citizens(
#         client: TestClient,
#         import_id: int,
#         expected_status: Union[int, EnumMeta] = HTTPStatus.OK,
#         **request_kwargs
# ) -> List[dict]:
#     response = await client.get(
#         url_for(CitizensView.URL_PATH, import_id=import_id),
#         **request_kwargs
#     )
#     assert response.status == expected_status
#
#     if response.status == HTTPStatus.OK:
#         data = await response.json()
#         errors = CitizensResponseSchema().validate(data)
#         assert errors == {}
#         return data['data']
#
