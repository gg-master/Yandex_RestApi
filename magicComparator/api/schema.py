"""
Модуль содержит схемы для валидации данных в запросах и ответах.

Схемы валидации запросов используются в бою для валидации данных отправленных
клиентами.

Схемы валидации ответов *ResponseSchema используются только при тестировании,
чтобы убедиться что обработчики возвращают данные в корректном формате.
"""
from datetime import datetime

from marshmallow import Schema, ValidationError, validates, validates_schema
from marshmallow.fields import Date, Dict, Int, Nested, Str, DateTime
from marshmallow.validate import Length, OneOf, Range

from magicComparator.db.schema import ShopUnitType


DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'


class ShopUnitSchema(Schema):
    id = Str(validate=Length(min=1, max=256), required=True)
    name = Str(validate=Length(min=1, max=256), required=True)
    parentId = Str(validate=Length(min=1, max=256), allow_none=True,
                   required=True)
    type = Str(validate=OneOf([u_type.value for u_type in ShopUnitType]),
               required=True)
    price = Int(validate=Range(min=0), strict=True, allow_none=True)

    @validates_schema
    def validate_price4type(self, data, **_):
        if data['type'] == ShopUnitType.offer.value and \
                data.get('price') is None:
            raise ValidationError(f"Unit: {data['id']} with type: "
                                  f"{data['type']} must have 'price'")
        if data['type'] == ShopUnitType.category.value and \
                (data.get('price') or data.get('price') == 0):
            raise ValidationError(f"Unit: {data['id']} with type: "
                                  f"{data['type']} mustn't have 'price'")


class ShopUnitsImportSchema(Schema):
    updateDate = DateTime(format=DATETIME_FORMAT, required=True)
    items = Nested(ShopUnitSchema, many=True, required=True,
                   validate=Length(max=10000))

    @validates_schema
    def validate_unique_shop_unit_id(self, data, **_):
        units_ids = set()
        for unit in data['items']:
            if unit['id'] in units_ids:
                raise ValidationError(
                    'id %r is not unique' % unit['id']
                )
            if unit['id'] == unit['parentId']:
                raise ValidationError(
                    'id %r can`t be self-parent' % unit['id']
                )
            units_ids.add(unit['id'])

    @validates('updateDate')
    def validate_update_date(self, value: datetime):
        if value > datetime.now():
            raise ValidationError("Update date can't be in future")


class ShopUnitsImportResponseSchema(Schema):
    data = Nested(ShopUnitsImportSchema(many=True), required=True)


class DeleteUnitSchema(Schema):
    id = Str(validate=Length(min=1, max=256), required=True)


class DeleteUnitResponseSchema(Schema):
    data = Nested(DeleteUnitSchema(), required=True)


class ShopUnitNodesSchema(Schema):
    id = Str(validate=Length(min=1, max=256), required=True)


class ShopUnitNodesResponseSchema(Schema):
    data = Nested(ShopUnitNodesSchema(), required=True)


class ShopUnitsSalesSchema(Schema):
    date = DateTime(format=DATETIME_FORMAT, required=True)


class ShopUnitSalesResponseSchema(Schema):
    data = Nested(ShopUnitsSalesSchema(), required=True)


class ShopUnitStatSchema(Schema):
    dateStart = DateTime(format=DATETIME_FORMAT)
    dateEnd = DateTime(format=DATETIME_FORMAT)

    @validates_schema
    def validate_date_interval(self, data, **_):
        if 'dateEnd' in data and data['dateEnd'] > datetime.now():
            raise ValidationError("dateEnd can't be in future")
        if 'dateEnd' in data and 'dateStart' in data and \
                data['dateEnd'] < data['dateStart']:
            raise ValidationError("dateEnd can't be earlier than dateStart")


class ShopUnitStatResponseSchema(Schema):
    data = Nested(ShopUnitStatSchema(), required=True)


class ErrorSchema(Schema):
    code = Str(required=True)
    message = Str(required=True)
    fields = Dict()


class ErrorResponseSchema(Schema):
    error = Nested(ErrorSchema(), required=True)
