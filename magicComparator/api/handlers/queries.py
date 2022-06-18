from sqlalchemy import func, select

from magicComparator.db.schema import category_table, category_parents_table, \
    offers_table, offers_parents_table
# Получение всех вложенных детей-категорий
ALL_CATEGORIES_CHILDREN_Q = '''
    WITH RECURSIVE category_children AS (
        SELECT parent_id, child_id AS id, category.date, name, type 
            FROM category_parents JOIN category 
            ON category.id = category_parents.child_id
        WHERE category_parents.parent_id = '{0}'
        UNION
        SELECT cp.parent_id, cp.child_id AS id, c.date, c.name, c.type 
            FROM category_parents cp JOIN category c ON c.id = cp.child_id
        JOIN category_children ON cp.parent_id = category_children.id
    )
    SELECT * FROM category_children
'''
# Получение актуальных вложенных детей-категорий
NOT_UPDATED_CATEGORIES_CHILDREN_Q = '''
    WITH RECURSIVE category_children AS (
        SELECT parent_id, child_id AS id, category.date, name, type 
            FROM category_parents JOIN category 
            ON category.id = category_parents.child_id
        WHERE category_parents.parent_id = '{0}' AND category.updated = false
        UNION
        SELECT cp.parent_id, cp.child_id AS id, c.date, c.name, c.type 
            FROM category_parents cp JOIN category c ON c.id = cp.child_id
        JOIN category_children ON cp.parent_id = category_children.id
        WHERE c.updated = false
    )
    SELECT * FROM category_children
'''
# Получение всех вложенных детей-товаров по переданному списку id категорий
ALL_OFFERS_CHILDREN_Q = '''
    SELECT parent_id, child_id AS id, offers.date, name, price, type 
    FROM offers_parents JOIN offers ON offers.id = offers_parents.child_id
    WHERE offers_parents.parent_id IN {0}
'''
# Получение всех актуальных вложенных детей-товаров по
# переданному списку id категорий
NOT_UPDATED_OFFERS_CHILDREN_Q = '''
    SELECT parent_id, child_id AS id, offers.date, name, price, type 
    FROM offers_parents JOIN offers ON offers.id = offers_parents.child_id
    WHERE offers_parents.parent_id IN {0} AND offers.updated = false
'''
AVG_PRICE_Q = '''
    WITH RECURSIVE categories_ids AS (
        SELECT child_id AS id FROM category_parents JOIN category 
            ON category.id = category_parents.child_id
        WHERE category_parents.parent_id = '{0}' AND category.updated = false
        UNION
        SELECT cp.child_id AS id FROM category_parents cp JOIN category c 
            ON c.id = cp.child_id
            JOIN categories_ids ON cp.parent_id = categories_ids.id
        WHERE c.updated = false
    )
    SELECT avg(price) 
    FROM offers_parents JOIN offers ON offers.id = offers_parents.child_id
    WHERE offers.updated = false AND offers_parents.parent_id IN 
    (SELECT id FROM categories_ids) OR offers_parents.parent_id = '{0}'
'''
# Получение полной информации о категорий
CATEGORY_QUERY = select([
    category_table.c.id,
    category_table.c.name,
    category_table.c.type,
    category_table.c.date,
    func.array_remove(
        func.array_agg(category_parents_table.c.parent_id),
        None
    ).label('parent_id')
]).select_from(category_table.outerjoin(
    category_parents_table,
    category_table.c.id == category_parents_table.c.child_id)
).group_by(
    category_table.c.id,
    category_table.c.name,
    category_table.c.type,
    category_table.c.date,
)
# Получение полной информации о товаре
OFFERS_QUERY = select([
    offers_table.c.id,
    offers_table.c.name,
    offers_table.c.type,
    offers_table.c.price,
    offers_table.c.date,
    func.array_remove(
        func.array_agg(offers_parents_table.c.parent_id),
        None
    ).label('parent_id')
]).select_from(offers_table.outerjoin(
    offers_parents_table,
    offers_table.c.id == offers_parents_table.c.child_id)
).group_by(
    offers_table.c.id,
    offers_table.c.name,
    offers_table.c.type,
    offers_table.c.price,
    offers_table.c.date,
)

