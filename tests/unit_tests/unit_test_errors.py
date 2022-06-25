# encoding=utf8

import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

# API_BASEURL = "https://flows-1989.usr.yandex-academy.ru"
API_BASEURL = "http://localhost:8081"

IMPORT_BAD_BATCHES = [
    # Отсутствует поле
    {
        "items": [
            {
                "type": "CATEGORY",
                "name": "Товары",
                "id": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",
            }
        ],
        "updateDate": "2022-05-01T12:00:00.000Z"
    },
    # Лишнее поле
    {
        "items": [{
            "type": "CATEGORY",
            "name": "Товары",
            "id": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",
            "parentId": None,
            "price": 0,
        }],
        "updateDate": "2022-05-01T12:00:00.000Z",
    },
    # Id родителя и юнита совпадают
    {
        "items": [
            {
                "type": "CATEGORY",
                "name": "Товары",
                "id": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",
                "parentId": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",
            }
        ],
        "updateDate": "2022-05-01T12:00:00.000Z"
    },
    # Неверный тип юнита
    {
        "items": [
            {
                "type": "category",
                "name": "Товары",
                "id": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",
                "parentId": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",
            }
        ],
        "updateDate": "2022-05-01T12:00:00.000Z"
    },
    # Неверный тип родителя
    {
        "items": [
            {
                "type": "CATEGORY",
                "name": "Товары",
                "id": "very-unique-category-id",
                "parentId": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",
            },
            {
                "type": "OFFER",
                "name": "smartphone1",
                "price": 1,
                "id": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",
                "parentId": None,
            }
        ],
        "updateDate": "2022-05-01T12:00:00.000Z"
    },
]


def request(path, method="GET", data=None, json_response=False):
    try:
        params = {
            "url": f"{API_BASEURL}{path}",
            "method": method,
            "headers": {},
        }

        if data:
            params["data"] = json.dumps(
                data, ensure_ascii=False).encode("utf-8")
            params["headers"]["Content-Length"] = len(params["data"])
            params["headers"]["Content-Type"] = "application/json"

        req = urllib.request.Request(**params)

        with urllib.request.urlopen(req) as res:
            res_data = res.read().decode("utf-8")
            if json_response:
                res_data = json.loads(res_data)
            return res.getcode(), res_data
    except urllib.error.HTTPError as e:
        return e.getcode(), None


def test_import_bad_req():
    # Ошибки валидации
    index = 0
    for index, batch in enumerate(IMPORT_BAD_BATCHES):
        print(f"Importing batch {index}")
        status, _ = request('/imports', method='POST', data=batch)
        assert status == 400, f"Expected HTTP status code 400, got {status}"

    index = iter(range(index + 1, 10))
    # Родитель юнита не найден
    print(f"Importing batch {next(index)}")
    data = {
        "items": [
            {
                "type": "CATEGORY",
                "name": "Товары",
                "id": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",
                "parentId": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1-notfound",
            }
        ],
        "updateDate": "2022-05-01T12:00:00.000Z"
    }

    status, _ = request('/imports', method='POST', data=data)
    assert status == 404, f"Expected HTTP status code 404, got {status}"

    # Два импорта подряд для тестирвоания проверки существования даты
    print(f"Importing batch {next(index)}")
    data = {
        "items": [
            {
                "type": "CATEGORY",
                "name": "Товары",
                "id": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",
                "parentId": None,
            }
        ],
        "updateDate": "2020-05-01T12:00:00.000Z"
    }
    status, _ = request('/imports', method='POST', data=data)
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    print(f"Importing batch {next(index)}")
    data = {
        "items": [
            {
                "type": "CATEGORY",
                "name": "Товары",
                "id": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",
                "parentId": None,
            }
        ],
        # Дата повторилась
        "updateDate": "2020-05-01T12:00:00.000Z"
    }
    status, _ = request('/imports', method='POST', data=data)
    assert status == 400, f"Expected HTTP status code 200, got {status}"

    print("Test import passed.")


def test_nodes_bad():
    # Искомого товара не существует
    status, response = request(f"/nodes/not-found-unit-id", json_response=True)
    assert status == 404, f"Expected HTTP status code 404, got {status}"

    print("Test nodes passed.")


def test_all():
    test_import_bad_req()
    test_nodes_bad()


def main():
    global API_BASEURL
    test_name = None

    for arg in sys.argv[1:]:
        if re.match(r"^https?://", arg):
            API_BASEURL = arg
        elif test_name is None:
            test_name = arg

    if API_BASEURL.endswith('/'):
        API_BASEURL = API_BASEURL[:-1]

    if test_name is None:
        test_all()
    else:
        test_func = globals().get(f"test_{test_name}")
        if not test_func:
            print(f"Unknown test: {test_name}")
            sys.exit(1)
        test_func()


if __name__ == "__main__":
    main()
