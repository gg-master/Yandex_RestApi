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


UPDATE_DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'


class UpdateDateTimeBaseSchema(Schema):
    updateDate = DateTime(format=UPDATE_DATETIME_FORMAT, required=True)

    @validates('updateDate')
    def validate_update_date(self, value: datetime):
        if value > datetime.now():
            raise ValidationError("Update date can't be in future")


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
        if data['type'] == ShopUnitType.offer.value and not data.get('price'):
            raise ValidationError(f"Unit: {data['id']} with type: "
                                  f"{data['type']} must have 'price'")
        if data['type'] == ShopUnitType.category.value and data.get('price'):
            raise ValidationError(f"Unit: {data['id']} with type: "
                                  f"{data['type']} mustn't have 'price'")


class ShopUnitsImportSchema(UpdateDateTimeBaseSchema):
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


class ShopUnitsSalesSchema(UpdateDateTimeBaseSchema):
    pass


class ShopUnitSalesResponseSchema(Schema):
    data = Nested(ShopUnitsSalesSchema(), required=True)


class ShopUnitStatSchema(Schema):
    id = Str(validate=Length(min=1, max=256), required=True)
    start_date = DateTime()
    end_date = DateTime()

    @validates_schema
    def validate_date_interval(self, data, **_):
        if 'end_data' in data and data['end_data'] > datetime.now():
            raise ValidationError("dateEnd can't be in future")
        if 'end_data' in data and 'start_date' in data and \
                data['end_data'] < data['start_date']:
            raise ValidationError("dateEnd can't be earlier than dateStart")


class ShopUnitStatResponseSchema(Schema):
    data = Nested(ShopUnitStatSchema(), required=True)


class ErrorSchema(Schema):
    code = Str(required=True)
    message = Str(required=True)
    fields = Dict()


class ErrorResponseSchema(Schema):
    error = Nested(ErrorSchema(), required=True)