# Репозиторий трасс сетевого трафика

Проект представляет собой программный репозиторий трасс сетевого трафика. Система предназначена для хранения сетевых трасс в формате `pcap`, трасс показателей качества обслуживания и интенсивности появления MAC-адресов в формате `csv`, а также связанных с ними метаданных, описаний, схем сбора и связей между исходными и производными трассами.

Репозиторий включает backend-приложение на FastAPI, базу данных PostgreSQL, файловое хранилище для трасс и сопутствующих файлов, а также frontend-приложение для работы пользователя через браузер.

## Необходимые программы

Перед первым запуском необходимо установить следующие программы:

1. **Docker Desktop** — для запуска PostgreSQL и backend-контейнера.
2. **Docker Compose** — обычно входит в Docker Desktop.
3. **Git** — для клонирования проекта.
4. **Node.js и npm** — для запуска frontend-приложения.
5. **Python 3.11+ или Python 3.12+** — нужен для локального запуска backend или тестов без Docker.
6. **DBeaver** — необязательно, но удобно для просмотра базы данных и выполнения SQL-запросов.

Проверить наличие основных программ можно командами:

```bash
docker compose version
git --version
node -v
npm -v
python --version
```


Все дальнейшие команды выполняются из корня проекта, если отдельно не указано другое.

## Настройка backend `.env`

Backend использует переменные окружения для подключения к базе данных, настройки JWT-токенов, файлового хранилища и создания администратора при первом запуске.

Создайте файл `.env` для backend. В зависимости от структуры проекта он может находиться в корне backend-папки или в той директории, которая используется как рабочая директория backend-контейнера.

Пример содержимого backend `.env`:

```env
POSTGRES_DB=trace_repo
POSTGRES_USER=trace_user
POSTGRES_PASSWORD=trace_pass
DATABASE_URL=postgresql+psycopg://trace_user:trace_password@db:5432/trace_repo

STORAGE_ROOT=/storage

JWT_SECRET=change_me_super_secret_value
JWT_ALG=HS256
ACCESS_TOKEN_EXPIRE_MIN=720

ADMIN_LOGIN=admin123
ADMIN_PASSWORD=some_vert_strong_pass_1234
ADMIN_FIRST_NAME=Name
ADMIN_LAST_NAME=Last_name
ADMIN_ORG=MSU
ADMIN_EMAIL=email@email.com
```

Описание обязательных переменных:

```text
POSTGRES_DB - имя БД, можно задавть свое, нужно согласовать со ссылкой на БД 
POSTGRES_USER - пользователь Бд, можно задать свое, нужно согласовать со ссылкой на БД
POSTGRES_PASSWORD - пароль пользователя БД, нужно согласовать со ссылкой на БД
DATABASE_URL — строка подключения к PostgreSQL, должжен быть согласован с POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
STORAGE_ROOT — путь к файловому хранилищу внутри контейнера.
JWT_SECRET — секретный ключ для подписи JWT-токенов.
JWT_ALG — алгоритм подписи JWT.
ACCESS_TOKEN_EXPIRE_MIN — время жизни access token в минутах.
ADMIN_LOGIN — логин администратора.
ADMIN_PASSWORD — пароль администратора.
ADMIN_FIRST_NAME — имя администратора.
ADMIN_LAST_NAME — фамилия администратора.
ADMIN_ORG — организация администратора.
ADMIN_EMAIL — e-mail администратора.
```

Важно: `ADMIN_LOGIN` должен содержать ровно 8 символов. Например:

```env
ADMIN_LOGIN=admin000
```
Важно, чтобы ссылка на БД выглядела так: 

```env
DATABASE_URL=postgresql+psycopg://trace_user:trace_pass@db:5432/trace_repo
```
```
trace_user - имя пользователя из POSTGRES_USER; 
trace_pass - пароль из POSTGRES_PASSWORD; 
trace_repo - имя БД из POSTGRES_DB; 
```

## Настройка frontend `.env`

В папке frontend создайте файл:

```text
.env
```
Содержимое:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Эта переменная нужна, чтобы frontend отправлял запросы на FastAPI backend, а не на порт Vite-приложения.

## Настройка CORS

frontend может запускаться на разных хостах, для это нужно разрешить подключение к хочу. В проете используется localhost:5173, однако лучше разрешить несколько хостов на случай, если localhost:5173 будет занят.

Пример настройки файла в `backend/app/main.py`:

```python
allow_origins=[
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
],
```

После изменения CORS backend нужно перезапустить. Если указанные порты окажутся заняты, то по аналогии приписать любой другой свободный порт и перезапустить проет. Если не указать в `backend/app/main.py` хост и запустить на нем frontend, то при попытке выполнения действий в репозитории будет возникать ошибка, например, faid to fetch. 

## Первый запуск через Docker Compose

Сначала запустите контейнеры:

```bash
docker compose up -d --build
```

Проверьте, что контейнеры запущены:

```bash
docker compose ps
```

Если backend падает из-за отсутствующих таблиц, это нормально для первого запуска до применения миграций. В таком случае можно сначала поднять только базу данных:

```bash
docker compose up -d db
```

## Применение миграций базы данных

После запуска backend необходимо применить миграции Alembic:

```bash
docker compose exec backend alembic upgrade head
```

Если backend-контейнер не запущен, можно выполнить миграции через одноразовый запуск контейнера:

```bash
docker compose run --rm backend alembic upgrade head
```

После применения миграций перезапустите backend:

```bash
docker compose restart backend
```

При старте backend создаёт администратора, если таблица пользователей уже существует и пользователя с логином из `ADMIN_LOGIN` ещё нет.

Интерактивная документация API доступна по адресу:

```text
http://localhost:8000/docs
```

## Первый запуск frontend

Перейдите в папку traffic-frontend из корня репозитория:

```bash
cd traffic-frontend
```

Установите зависимости:

```bash
npm install
```

Запустите frontend:

```bash
npm run dev
```

Обычно Vite запускает приложение на:

```text
http://localhost:5173
```

Если порт `5173` занят, Vite может выбрать следующий свободный порт, например `5174`. В таком случае этот адрес должен быть добавлен в CORS backend.

## Вход в систему

Откройте frontend в браузере:

```text
http://localhost:5173
```

или другой порт, который показал Vite.

Данные администратора по умолчанию хранятся .env

Если в `.env` был задан другой `ADMIN_PASSWORD`, нужно использовать его.


## Запуск backend-тестов

В проекте есть тесты на `pytest`, их можно запустить внутри backend-контейнера:

```bash
docker compose exec backend pytest tests 
```


## Проверка frontend

В папке traffic-frontend выполнить:

```bash
npm install
npm run dev
```

## Нагрузочное тестирование

Из корня проекта выполнить: 
```
python backend/loadtests/run_series.py
```

После завершения всех тестов можно выполнить дял построения итоговой таблицы: 
```
python backend/loadtests/render_results.py
```

## Освобождение занятых портов

Если при перезапуске frontend порт оказался занят, можно найти процесс:

```bash
lsof -i :5173
```

или:

```bash
lsof -i :5174
```

Завершитьт процесс:

```bash
kill -9 <PID>
```

Быстро освободить порт:

```bash
lsof -ti :5173 | xargs kill -9
lsof -ti :5174 | xargs kill -9
```

Для backend-порта:

```bash
lsof -ti :8000 | xargs kill -9
```

## Частые проблемы первого запуска

### Backend не подключается к базе данных

Нужно проверить `DATABASE_URL`.

```env
DATABASE_URL=postgresql+psycopg://trace_user:trace_password@db:5432/trace_repo
```

### Ошибка CORS

Если frontend открыт на `http://localhost:5174`, а backend разрешает только `http://localhost:5173`, браузер заблокирует запросы.

Нужно добавить `5174` в `allow_origins` и перезапустить backend.

### Таблицы не создались

Выполнить миграции:

```bash
docker compose exec backend alembic upgrade head
docker compose restart backend
```

### Администратор не создался

Нужно проверить:

1. миграции применены;
2. таблица `users` существует;
3. `ADMIN_LOGIN` содержит ровно 8 символов;
4. backend был перезапущен после применения миграций.

Проверить пользователей можно через DBeaver:

```sql
SELECT id, login, role
FROM users;
```

## Короткая последовательность первого запуска

```bash
docker compose up -d --build
docker compose exec backend alembic upgrade head
docker compose restart backend
cd traffic-frontend
npm install (при певром запуске frontend)
npm run dev
```

После этого открыть frontend в браузере:

```text
http://localhost:5173
```

и войти под администратором.
