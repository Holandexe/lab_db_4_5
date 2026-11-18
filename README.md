# tickets.ua — Back-End (Flask + Python + MySQL)

Лабораторна робота №4, варіант 14. Back-End для бази даних `tickets_ua` (лаб. №1 та №3): квитки на події,
артисти, місця, замовлення, доставка, оплата, транспортні квитки.

## Архітектура

```
config/app.yml            – налаштування сервера та підключення до MySQL
my_project/
  __init__.py             – create_app(): конфіг, маршрути, обробка помилок (JSON)
  auth/
    domain/               – сутності (entities.py) та DTO (dto.py)
    dao/                  – усі SQL-запити (base_dao.py = CRUD, daos.py = спеціальні запити)
    service/              – бізнес-логіка та валідація (base_service.py, services.py)
    controller/           – обробка HTTP-запитів, повернення DTO
    route/                – URL -> контролери, збирання залежностей
  ui/templates/index.html – сторінка зі списком усіх маршрутів
  utils/                  – підключення до БД (db.py), винятки (errors.py)
tests/test_api.py         – автотести (pytest)
data.sql                  – скрипт створення БД і даних (лаб. №3)
postman_collection.json   – колекція для тестування в Postman
```
Потік даних: **Route → Controller → Service → DAO → MySQL**, назад — **Entity → DTO → JSON**.

## Запуск

1. Створити БД: виконати `data.sql` у MySQL Workbench (або `mysql -u root -p < data.sql`).
2. Вказати логін/пароль MySQL у `config/app.yml` (або змінні оточення `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`).
3. Встановити залежності та запустити:
```bash
python -m venv venv
venv\Scripts\activate          # Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
python app.py
```
Сервер: http://127.0.0.1:5000 (на `/` — список усіх маршрутів).

## Основні маршрути (префікс `/api`)

| Що | Маршрути |
|---|---|
| CRUD (17 таблиць) | `GET/POST /{countries, cities, venues, event-types, artists, events, seats, event-seats, customers, delivery-options, payment-methods, orders, tickets, transport-routes, transport-tickets, payments}` та `GET/PUT/PATCH/DELETE /<resource>/<id>` |
| M:1 (батько → діти) | `/countries/<id>/cities`, `/cities/<id>/venues`, `/venues/<id>/events`, `/customers/<id>/orders`, `/orders/<id>/tickets`, `/events/<id>/seats` та ін. |
| M:N (event ↔ artist) | `GET /events/<id>/artists`, `GET /artists/<id>/events`, `POST /events/<id>/artists`, `DELETE /events/<id>/artists/<artist_id>`, `GET /event-artists` |
| Бізнес-логіка | `GET /events/<id>/seats/available`, `GET /orders/<id>/summary`, покупка квитка `POST /tickets` (місце → `sold`), повернення `DELETE /tickets/<id>` (місце → `available`), `POST /payments` без `amount` бере суму замовлення |

Коди відповідей: `200/201` успіх, `400` помилка валідації, `404` не знайдено, `409` конфлікт (UNIQUE / FOREIGN KEY / місце вже продане).

## Тестування

* **Postman:** Import → `postman_collection.json`, змінна `base_url = http://127.0.0.1:5000`. Папки запускати по порядку 1→6
  (Collection Runner). Створені id зберігаються в змінних колекції автоматично.
* **pytest:** `python -m pytest -q tests`

## GitHub

```bash
git init
git add .
git commit -m "Lab 4: Flask back-end for tickets_ua"
git branch -M main
git remote add origin https://github.com/<your-login>/tickets-ua-backend.git
git push -u origin main
```
