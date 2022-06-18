"""Initial

Revision ID: e429cf8e57c2
Revises: 
Create Date: 2022-06-17 21:51:50.322717

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e429cf8e57c2'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('update_dates',
    sa.Column('date', sa.DateTime(), nullable=True)
    )
    op.create_index(op.f('ix__update_dates__date'), 'update_dates', ['date'], unique=True)
    op.create_table('category',
    sa.Column('date', sa.DateTime(), nullable=False),
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('type', sa.Enum('offer', 'category', name='type'), nullable=True),
    sa.Column('updated', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['date'], ['update_dates.date'], name=op.f('fk__category__date__update_dates')),
    sa.PrimaryKeyConstraint('date', 'id', name=op.f('pk__category'))
    )
    op.create_index(op.f('ix__category__id'), 'category', ['id'], unique=False)
    op.create_table('offers',
    sa.Column('date', sa.DateTime(), nullable=False),
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('type', sa.Enum('offer', 'category', name='type'), nullable=True),
    sa.Column('price', sa.Integer(), nullable=False),
    sa.Column('updated', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['date'], ['update_dates.date'], name=op.f('fk__offers__date__update_dates')),
    sa.PrimaryKeyConstraint('date', 'id', name=op.f('pk__offers'))
    )
    op.create_index(op.f('ix__offers__id'), 'offers', ['id'], unique=False)
    op.create_table('category_parents',
    sa.Column('date', sa.DateTime(), nullable=False),
    sa.Column('parent_id', sa.String(), nullable=False),
    sa.Column('child_id', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['date', 'child_id'], ['category.date', 'category.id'], name=op.f('fk__category_parents__date_child_id__category')),
    sa.ForeignKeyConstraint(['date', 'parent_id'], ['category.date', 'category.id'], name=op.f('fk__category_parents__date_parent_id__category')),
    sa.PrimaryKeyConstraint('date', 'parent_id', 'child_id', name=op.f('pk__category_parents'))
    )
    op.create_table('offers_parents',
    sa.Column('date', sa.DateTime(), nullable=False),
    sa.Column('parent_id', sa.String(), nullable=False),
    sa.Column('child_id', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['date', 'child_id'], ['offers.date', 'offers.id'], name=op.f('fk__offers_parents__date_child_id__offers')),
    sa.ForeignKeyConstraint(['date', 'parent_id'], ['category.date', 'category.id'], name=op.f('fk__offers_parents__date_parent_id__category')),
    sa.PrimaryKeyConstraint('date', 'parent_id', 'child_id', name=op.f('pk__offers_parents'))
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('offers_parents')
    op.drop_table('category_parents')
    op.drop_index(op.f('ix__offers__id'), table_name='offers')
    op.drop_table('offers')
    op.drop_index(op.f('ix__category__id'), table_name='category')
    op.drop_table('category')
    op.drop_index(op.f('ix__update_dates__date'), table_name='update_dates')
    op.drop_table('update_dates')
    # ### end Alembic commands ###