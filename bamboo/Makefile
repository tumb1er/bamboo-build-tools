#
# Основной Makefile сборщика для bamboo
#
# Пример вызова: make -e PROJECT_NAME=<project_name> <target>
#

# Общая директория проектов
DATA_DIR:=/data

# Ссылка на локальный репозиторий
DIST_URL:=http://y.rutube.ru/vrepo/dist

# Текущая рабочая директория
WORKING_DIR:=$(shell pwd)

# Директория с исходными файлами проекта
SOURCES_DIR:=$(WORKING_DIR)

ifndef PROJECT_NAME
    $(error missing variable: make -e PROJECT_NAME=<project>)
endif

ifndef PROJECT_MK
    $(warning PROJECT_MK not defined, no extra actions will be executed)
else
    include $(PROKECT_MK)
endif

# Корневая директория проекта:
PROJECT_DIR:=$(DATA_DIR)/$(PROJECT_NAME)

# Директория виртуального окружения
VENV_DIR:=$(PROJECT_DIR)/virtualenv

# Команда активации виртуального окружения
ACTIVATE=. $(VENV_DIR)/bin/activate

# Команда установки из локального репозитория
PIP_INSTALL:=pip install -f $(DIST_URL)

# Команда установки из файла
PIP_REQUIRES=$(PIP_INSTALL) -r $(SOURCES_DIR)/$(R);

# Команда запуска coverage
COVERAGE_CMD=python -m coverage run $(COVERAGE_ARGS)

# Команда запуска тестов Django
MANAGE_CMD=$(MANAGE_SCRIPT) test $(NOSE_ARGS)

# Список файлов requires
REQUIRES:=requires.part1.txt requires.part2.txt
REQUIRES_DEV:=requires.dev.txt
REQUIRES_TEST:=requires.test.txt

# Название файла локальных настроек проекта
SETTINGS_LOCAL=settings_local_$(PROJECT_NAME).py

# Путь до manage.py для Django-проектов
MANAGE_SCRIPT=./manage.py

# Аргументы запуска coverage
COVERAGE_ARGS:= --branch --source=$(WORKING_DIR) --omit="*/migrations/*,*/virtualenv/*"

# Аргументы запуска nosetests
NOSE_ARGS:= --verbosity=0 --with-xunit

REPORTS_DIR:=.reports
COVERAGE_XML:=$(REPORTS_DIR)/coverage.xml
CLOVER_XML:=$(REPORTS_DIR)/clover.xml
COVERAGE_HTML:=$(REPORTS_DIR)
#
QUITE_CMD:= 1>/dev/null 2>/dev/null || exit

# Имя цели для "раскатки в текущую директорию"
# Если исходники лежат в текущей директории, ничего копировать не надо
ifeq ($(WORKING_DIR), $(SOURCES_DIR))
    COPY_CWD_TARGET:=skip-copy
else
    COPY_CWD_TARGET:=copy-cwd
endif

# Запускать ли тесты вместе со сбором coverage
ifdef WITH_COVERAGE
    DJANGO_TEST_TARGET:=coverage-django-tests
else
    DJANGO_TEST_TARGET:=run-django-tests
endif

ifdef $(TEST_PROCESSES)
    COVERAGE_ARGS+= --parallel-mode
    NOSE_ARGS+= --processes=$(TEST_PROCESSES)
endif


# Основные цели

# Установка на продакшн
# =====================
#
# Создает все директории,
# устанавливает проект в DATA_DIR,
# создает виртуальное окружение,
# ставит зависимости,
# настраивает rc-скрипты

deploy-admin: copy-project deploy-basic rcscripts $(POST_DEPLOY_ADMIN_TARGETS)
	$(info ADMIN DEPLOYING FINISHED SUCCESSFULLY)

# Установка на машине разработчика
# ================================
#
# Отличается от установки на продакшн тем, что
# развертывает виртуальное окружение и проект в текущей папке,
# пропускает настройку rc-скриптов и
# устанавливает дополнительные пакеты
#

deploy-devel: $(COPY_CWD_TARGET) deploy-basic requires-dev $(POST_DEPLOY_DEVEL_TARGETS)
	$(info DEVEL DEPLOYING FINISHED SUCCESSFULLY)

# Развертывание пакета для тестов
# ===============================
#
# Аналогично установки на продакшн, но
# развертывает виртуальное окружение и проект в текущей папке,
# пропускает настройку rc-скриптов и
# ставит дополнительные пакеты для тестирования
#

deploy-test: $(COPY_CWD_TARGET) deploy-basic requires-test symlinks $(POST_DEPLOY_TEST_TARGETS)
	$(info TEST DEPLOYING FINISHED SUCCESSFULLY)

# Запуск тестов для Django-проекта
# ================================
#
# запускает management-команду запуска тестов

test-django: $(DJANGO_TEST_TARGET)
	$(info DJANGO TESTS COMPLETED)

# Служебные цели
# ===============================

# Варианты копирования файлов проекта
# -----------------------------------

# Вообще не копировать (из CWD в CWD)
skip-copy:
	$(info file copy not needed)
# Копировать в CWD из папки SOURCES_DIR
copy-cwd:
	cp -R $(SOURCES_DIR)/* .
# Копировать из папки SOURCES_DIR в PROJECT_DIR
copy-project: project_dir
	cp -R $(SOURCES_DIR)/* $(PROJECT_DIR)

project_dir:
	mkdir -p $(PROJECT_DIR)

# Процесс развертывания
# ---------------------

deploy-basic: virtualenv requires

virtualenv:
	virtualenv --system-site-packages $(VENV_DIR)

requires:
	$(ACTIVATE); $(foreach R, $(REQUIRES), $(PIP_REQUIRES))

requires-dev:
	$(ACTIVATE); $(foreach R, $(REQUIRES_DEV), $(PIP_REQUIRES))

requires-test:
	$(ACTIVATE); $(foreach R, $(REQUIRES_TEST), $(PIP_REQUIRES))

symlinks:
	ln -sf $(DATA_DIR)/$(SETTINGS_LOCAL) $(WORKING_DIR)/..

rcscripts:
	echo RCSCRIPTS
	$(info RCSCRIPTS)

# Процесс тестирования
# --------------------

coverage-django-tests: clean-reports report-dir
	echo "Running Django tests with coverage"
	$(ACTIVATE); $(COVERAGE_CMD) $(MANAGE_CMD) $(QUITE_CMD)
	coverage combine
	coverage xml -o $(COVERAGE_XML)
	coverage html -d $(COVERAGE_HTML)
	coverage2clover -i $(COVERAGE_XML) -o $(CLOVER_XML)

run-django-tests:
	echo "Running Django tests"
	$(ACTIVATE); python $(MANAGE_CMD) $(DJANGO_APPS) $(QUITE_CMD)

report-dir:
	mkdir -p $(REPORTS_DIR)

clean-reports:
	rm -r $(REPORTS_DIR) || exit
