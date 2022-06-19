PROJECT_NAME ?= yandex_rest_api
VERSION = $(shell python3 setup.py --version | tr '+' '-')
PROJECT_NAMESPACE ?= mekop
REGISTRY_IMAGE ?= $(PROJECT_NAMESPACE)/$(PROJECT_NAME)

all:
	@echo "make devenv		- Create & setup development virtual environment"
	@echo "make postgres	- Start postgres container"
	@echo "make clean		- Remove files created by distutils"
	@echo "make sdist		- Make source distribution"
	@echo "make docker		- Build a docker image"
	@echo "make upload		- Upload docker image to the registry"
	@exit 0

clean:
	rm -fr *.egg-info dist

devenv: clean
	rm -rf env
	# создаем новое окружение
	python3.8 -m venv env
	# обновляем pip
	env/bin/pip install -U pip
	# устанавливаем основные + dev зависимости из extras_require (см. setup.py)
	env/bin/pip install -Ue '.[dev]'

postgres:
	docker stop magicComparator-postgres || true
	docker run --rm --detach --name=magicComparator-postgres \
		--env POSTGRES_USER=postgres \
		--env POSTGRES_PASSWORD=postgrespwd \
		--env POSTGRES_DB=magic_comp_db \
		--publish 5434:5432 postgres

sdist: clean
	# официальный способ дистрибуции python-модулей
	python3 setup.py sdist

docker: sdist
    # docker build --target=api -t yandex_rest_api:0.0.1 .
	docker build --target=api -t $(PROJECT_NAME):$(VERSION) .

upload: docker
    # docker tag yandex_rest_api:0.0.1 mekop/yandex_rest_api:0.0.1
    # docker tag yandex_rest_api:0.0.1 mekop/yandex_rest_api:latest
    # docker push mekop/yandex_rest_api:0.0.1
    # docker push mekop/yandex_rest_api:latest
	docker tag $(PROJECT_NAME):$(VERSION) $(REGISTRY_IMAGE):$(VERSION)
	docker tag $(PROJECT_NAME):$(VERSION) $(REGISTRY_IMAGE):latest
	docker push $(REGISTRY_IMAGE):$(VERSION)
	docker push $(REGISTRY_IMAGE):latest