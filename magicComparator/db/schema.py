from enum import Enum, unique

from sqlalchemy import (
    Column, Enum as PgEnum, Integer, Boolean, DateTime,
    MetaData, String, Table, ForeignKey, ForeignKeyConstraint
)

convention = {
    'all_column_names': lambda constraint, table: '_'.join([
        column.name for column in constraint.columns.values()
    ]),
    'ix': 'ix__%(table_name)s__%(all_column_names)s',
    'uq': 'uq__%(table_name)s__%(all_column_names)s',
    'ck': 'ck__%(table_name)s__%(constraint_name)s',
    'fk': 'fk__%(table_name)s__%(all_column_names)s__%(referred_table_name)s',
    'pk': 'pk__%(table_name)s'
}

metadata = MetaData(naming_convention=convention)


@unique
class ShopUnitType(Enum):
    offer = 'OFFER'
    category = 'CATEGORY'


updateDates = Table(
    'update_dates',
    metadata,
    Column('date', DateTime, unique=True, index=True)
)


offers_table = Table(
    'offers',
    metadata,
    Column('date', DateTime, ForeignKey('update_dates.date'), primary_key=True),
    Column('id', String, nullable=False, primary_key=True, index=True),
    Column('name', String, nullable=False),
    Column('price', Integer, nullable=False),
    Column('updated', Boolean, default=False),
)

category_table = Table(
    'category',
    metadata,
    Column('date', DateTime, ForeignKey('update_dates.date'), primary_key=True),
    Column('id', String, nullable=False, primary_key=True, index=True),
    Column('name', String, nullable=False),
    Column('updated', Boolean, default=False),
)

offers_parents_table = Table(
    'offers_parents',
    metadata,
    Column('date', DateTime, primary_key=True),
    Column('parent_id', String, primary_key=True),
    Column('child_id', String, primary_key=True),
    ForeignKeyConstraint(
        ('date', 'parent_id'),
        ('category.date', 'category.id')
    ),
    ForeignKeyConstraint(
        ('date', 'child_id'),
        ('offers.date', 'offers.id')
    ),
)

category_parents_table = Table(
    'category_parents',
    metadata,
    Column('date', DateTime, primary_key=True),
    Column('parent_id', String, primary_key=True),
    Column('child_id', String, primary_key=True),
    ForeignKeyConstraint(
        ('date', 'parent_id'),
        ('category.date', 'category.id')
    ),
    ForeignKeyConstraint(
        ('date', 'child_id'),
        ('category.date', 'category.id')
    ),
)

unit_tables_association = {
    ShopUnitType.offer: offers_table,
    ShopUnitType.category: category_table
}

parent_tables_association = {
    ShopUnitType.offer: offers_parents_table,
    ShopUnitType.category: category_parents_table
}
