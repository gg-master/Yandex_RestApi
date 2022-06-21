Rest Api приложение, для вступительного задания в Школу бэкенд разработки Яндекса в 2022 году.

Приложение свернуто в Docker-контейнер. В нем доступны две команды:
1. `magicComparator-db` - утилита для управления состоянием бд. 
2. `magicComparator-api` - утилита для запуска сервиса.

<h2>Использование</h2>
* Запустить локально можно как из Docker-контейнера, следующей командой:
``` 
docker run -it -p 8081:8081 -e MAGIC_COMPARATOR_PG_URL=postgresql://postgres1:postgrespwd@localhost:5434/magic_comp_db mekop/yandex_rest_api
```
Или в самом проекте, командой: 
```
magicComparator-api
```
---
* Применить миграции можно аналогичными командами:
```
docker run -it -e MAGIC_COMPARATOR_PG_URL=postgresql://postgres1:postgrespwd@localhost:5434/magic_comp_db mekop/yandex_rest_api magicComparator-db
```
<i>Или</i> 
```
magicComparator-db upgrade head
```
---
Все доступные опции можно просмотреть следующими командами:
```
docker run mekop/yandex_rest_api magicComparator-db --help
docker run mekop/yandex_rest_api magicComparator-api --help
```

<h2>Деплой</h2>
Развернуть сервис можно 2 способами:
1. Использовав ansible. <br>
    Для этого вам необходимо добавить список серверов в файл deploy/hosts.ini 
    (с установленной Ubuntu) и выполнить команды:
    ```
    cd deploy
    ansible-playbook -i hosts.ini --user=root deploy.yml
    ```
2. Использовава docker-compose. Для этого вам необходимо создать .yml файл со следующим содержанием
    ```yaml
    version : '3'
    services:
    
      server:
        container_name: DEV-SERVER
        image: mekop/yandex_rest_api
        restart: always
        environment:
          MAGIC_COMPARATOR_PG_URL: postgresql://postgres_user:postgrespwd@postgres-server/magic_comparator_db
          POSTGRES_USER: postgres_user
          POSTGRES_PASSWORD: postgrespwd
          POSTGRES_DB: magic_comparator_db
        ports:
          - "80:8081"
        depends_on:
          postgres-server:
            condition: service_healthy
    
      postgres-server:
        image: postgres:14
        container_name: POSTGRES-SERVER
        restart: always
        environment:
          POSTGRES_DB: "magic_comparator_db"
          POSTGRES_USER: "postgres_user"
          POSTGRES_PASSWORD: "postgrespwd"
        ports:
          - "5432:5432"
        healthcheck:
          test: ["CMD-SHELL", "pg_isready -d magic_comparator_db -U postgres_user"]
          interval: 10s
          timeout: 5s
          retries: 5
    ```
   И запустить команду `docker-compose up` в директории с созданным вами .yml файлом.
   