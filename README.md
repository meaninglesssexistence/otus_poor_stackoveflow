# Hasker: Poor Man's Stackoverflow

Задание: Написать Q&A сайт, аналог stackoverflow.com. Это будет Django
приложение, поĸрытое тестами.

Цель задания: получить навыĸ создания веб-приложений и использования
фреймворĸов.

Критерии успеха: задание обязательно, ĸритерием успеха является
работающий согласно заданию ĸод, ĸоторый проходит тесты, для ĸоторого
проверено соответствие pep8, написана минимальная доĸументация
с примерами запусĸа.

## Ссылка на проект

[Hasker: Poor Man's Stackoverflow](https://poor-stackoverflow.herokuapp.com/hasker/)

## Проектные решения

- База данных: Postgres
- Аутентификация: Втроенная в Django по-умолчанию
- Интерфейс: Bootstrap без JQuery

## Локальное развертывание системы

1. Скачать исходники с GitHub-а

2. Опционально создать virtual environment

3. Установить Postgress

```
$ apt install postgresql-13 postgresql-client-13
```

4. Установить пакеты Python

```
$ pip install -r requirements.txt
```

5. Создать базу данных

```
$ sudo -u postgres psql -c 'create database hasker-db;'
```

6. Создать и отредактировать файл с рабочими настройками

```
$ cp stackoverflow/example.env stackoverflow/.env
```

7. Провести миграцию базы данных

```
$ manage.py migrate
```

### Запуск сервера

```
$ manage.py runserver
```

### Запуск тестов

```
$ manage.py test
```

## Continious integration

CI настроен на [Travis CI](https://www.travis-ci.com/). Настройки в
файле [.travis.yml](.travis.yml). Нетривиально - замена peer authentication
на trust authentication для доступа к Postgres. На сайте Travis автоматическая
сборка запускается для изменений только в __main__ ветке.

## Continious deployment

CD настроен на [Heroku](https://www.heroku.com). Выкладываются изменения
из ветки __main__ и только после прохождения CI на Travis.

Для настройки Heroku использованы следующие команды:

```
# Создание приложения
$ heroku create poor-stackoverflow
# Подключение/создание Postgres сервера
$ heroku addons:create heroku-postgresql:hobby-dev
```

Настроены следующие переменные среды:

| Название              | Значение                                         |
| -------------         | ------------------------------------------------ |
| ALLOWED_HOSTS         | 0.0.0.0,localhost,127.0.0.1,poor-stackoverflow.herokuapp.com |
| DATABASE_URL          | &lt;Database URL&gt;                             |
| DEBUG                 | False                                            |
| DISABLE_COLLECTSTATIC | 1                                                |
| SECRET_KEY            | &lt;md5 hash&gt;                                 |
