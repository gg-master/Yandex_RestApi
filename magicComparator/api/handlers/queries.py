# Получение всех вложенных детей-категорий
ALL_CATEGORIES_CHILDREN_Q = '''
    WITH RECURSIVE category_children AS (
        SELECT parent_id, child_id AS id, category.date, name, 'CATEGORY' as type 
            FROM category_parents JOIN category 
            ON category.id = category_parents.child_id
        WHERE category_parents.parent_id = '{0}'
        UNION
        SELECT cp.parent_id, cp.child_id AS id, c.date, c.name, 'CATEGORY' as type
            FROM category_parents cp JOIN category c ON c.id = cp.child_id
        JOIN category_children ON cp.parent_id = category_children.id
    )
    SELECT * FROM category_children
'''
# Получение актуальных вложенных детей-категорий
NOT_UPDATED_CATEGORIES_CHILDREN_Q = '''
    WITH RECURSIVE category_children AS (
        SELECT parent_id as "parentId", child_id AS id, category.date, name, 
            'CATEGORY' as type
            FROM category_parents JOIN category 
            ON category.id = category_parents.child_id
        WHERE category_parents.parent_id = '{0}' AND category.updated = false
        UNION
        SELECT cp.parent_id as "parentId", cp.child_id AS id, c.date, c.name, 
            'CATEGORY' as type
            FROM category_parents cp JOIN category c ON c.id = cp.child_id
        JOIN category_children ON cp.parent_id = category_children.id
        WHERE c.updated = false
    )
    SELECT * FROM category_children
'''
# Получение всех вложенных детей-товаров по переданному списку id категорий
ALL_OFFERS_CHILDREN_Q = '''
    SELECT parent_id, child_id AS id, offers.date, name, price, 'OFFER' as type 
    FROM offers_parents JOIN offers ON offers.id = offers_parents.child_id
    WHERE offers_parents.parent_id IN {0}
'''
# Получение всех актуальных вложенных детей-товаров по
# переданному списку id категорий
NUP_OFFERS_CHILD_Q = '''
    SELECT parent_id as "parentId", child_id AS id, offers.date, name, price, 
    'OFFER' as type, null as children
    FROM offers_parents JOIN offers ON offers.id = offers_parents.child_id
    WHERE offers_parents.parent_id IN ('{0}') AND offers.updated = false
'''
# Высчитывание средней цены для категории по ее id
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
CATEGORY_Q = '''
SELECT id, name, category.date, 'CATEGORY' as type, null as price, 
category_parents.parent_id AS "parentId"
FROM category LEFT OUTER JOIN category_parents 
ON category_parents.child_id = category.id
WHERE category.id = '{0}' AND category.updated = false
'''

# Получение полной информации о товаре
OFFERS_Q = '''
SELECT id, name, offers.date, 'OFFER' as type, price, 
offers_parents.parent_id AS "parentId"
FROM offers LEFT OUTER JOIN offers_parents 
ON offers_parents.child_id = offers.id
WHERE offers.id = '{0}' AND offers.updated = false
'''

# Получение товаров, которые обновлялись в указанный промежуток времени
OFFERS_SALES_Q = '''
WITH updated_offers as (
    SELECT DISTINCT id FROM offers
    WHERE offers.date BETWEEN '{date_start}' AND '{date_end}'
)
SELECT id, name, offers.date, 'OFFER' as type, price, 
offers_parents.parent_id AS "parentId"
FROM offers LEFT OUTER JOIN offers_parents 
ON offers_parents.child_id = offers.id
WHERE offers.id in (SELECT id FROM updated_offers) AND offers.updated = false

'''
# Получение статистики по категории
CATEGORY_STAT_Q = '''
SELECT id, name, 'CATEGORY' AS "type", category.date, null as "price",
category_parents.parent_id AS "parentId"
FROM category LEFT OUTER JOIN category_parents 
ON category_parents.child_id = category.id 
AND category.date = category_parents.date
WHERE category.id = '{uid}' AND 
    category.date BETWEEN '{date_start}' AND '{date_end}'
'''
# Получение статистики по товару
OFFER_STAT_Q = '''
SELECT id, name, 'OFFER' AS "type", offers.date, price, 
offers_parents.parent_id AS "parentId"
FROM offers LEFT OUTER JOIN offers_parents 
ON offers_parents.child_id = offers.id AND offers.date = offers_parents.date
WHERE offers.id = '{uid}' AND 
    offers.date BETWEEN '{date_start}' AND '{date_end}'
'''
# Высчитывание средней цены для товаров по дате
AVG_PRICE_BY_DATE = '''
WITH RECURSIVE categories_ids AS (
    SELECT child_id AS id FROM category_parents JOIN category 
        ON category.id = category_parents.child_id
    WHERE category_parents.parent_id = '{uid}' AND category.date <= '{date_end}'
    UNION
    SELECT cp.child_id AS id FROM category_parents cp JOIN category c 
        ON c.id = cp.child_id
        JOIN categories_ids ON cp.parent_id = categories_ids.id
    WHERE c.date <= '{date_end}'
)   
SELECT floor(avg(price)) FROM offers JOIN (
    SELECT p1.date, p1.child_id
    FROM offers_parents p1 LEFT OUTER JOIN offers_parents p2 
        ON (p1.child_id = p2.child_id) AND (p1.date < p2.date 
                                            AND p1.date < '{date_end}')
    WHERE p2.date IS NULL AND (p1.parent_id IN (SELECT id FROM categories_ids) 
    OR p1.parent_id = '{uid}') AND p1.date <= '{date_end}'
) t ON t.date = offers.date AND t.child_id = offers.id
'''