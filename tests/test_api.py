"""Інтеграційні тести API. Потрібна запущена MySQL з БД tickets_ua (data.sql).
Параметри підключення беруться з config/app.yml або змінних оточення DB_USER / DB_PASSWORD."""
import uuid

import pytest

from my_project import create_app


@pytest.fixture(scope="module")
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def uniq(prefix="t"):
    return f"{prefix}-{uuid.uuid4().hex[:6]}"


# ---------- READ ----------
@pytest.mark.parametrize("path", [
    "countries", "cities", "venues", "event-types", "artists", "events", "seats", "event-seats", "customers",
    "delivery-options", "payment-methods", "orders", "tickets", "transport-routes", "transport-tickets",
    "payments", "event-artists"])
def test_list_all_tables(client, path):
    r = client.get(f"/api/{path}")
    assert r.status_code == 200
    assert len(r.get_json()) >= 10


def test_get_one_and_404(client):
    assert client.get("/api/countries/1").get_json()["iso_code"] == "UA"
    r = client.get("/api/countries/99999")
    assert r.status_code == 404 and "error" in r.get_json()


def test_pagination(client):
    assert len(client.get("/api/cities?limit=3&offset=2").get_json()) == 3


# ---------- CREATE / UPDATE / DELETE ----------
def test_crud_country(client):
    code = uniq("X")[:2].upper()
    r = client.post("/api/countries", json={"name": uniq("Land"), "iso_code": code})
    assert r.status_code == 201
    cid = r.get_json()["id"]
    r = client.put(f"/api/countries/{cid}", json={"name": "Newland", "iso_code": code})
    assert r.status_code == 200 and r.get_json()["name"] == "Newland"
    r = client.patch(f"/api/countries/{cid}", json={"name": "Patchland"})
    assert r.get_json()["name"] == "Patchland"
    assert client.delete(f"/api/countries/{cid}").status_code == 200
    assert client.get(f"/api/countries/{cid}").status_code == 404


def test_validation_errors(client):
    assert client.post("/api/countries", json={"name": "NoIso"}).status_code == 400          # missing field
    assert client.post("/api/countries", json={"name": "A", "iso_code": "ZZ", "bad": 1}).status_code == 400
    assert client.post("/api/venues", json={"city_id": "x", "name": "n", "address": "a", "capacity": 5}).status_code == 400
    assert client.post("/api/countries", data="not json").status_code == 400


def test_constraints(client):
    assert client.post("/api/countries", json={"name": "Ukraine", "iso_code": "QQ"}).status_code == 409   # UNIQUE
    assert client.post("/api/cities", json={"country_id": 9999, "name": "Ghost"}).status_code == 409      # FK
    assert client.delete("/api/countries/1").status_code == 409                                           # used by FK


# ---------- M:1 ----------
def test_one_to_many(client):
    data = client.get("/api/countries/1/cities").get_json()
    assert data["parent"]["name"] == "Ukraine" and data["count"] >= 5
    assert all(c["country_id"] == 1 for c in data["cities"])
    assert client.get("/api/customers/1/orders").get_json()["count"] >= 1
    assert client.get("/api/orders/3/tickets").get_json()["count"] == 2
    assert client.get("/api/countries/99999/cities").status_code == 404


# ---------- M:N ----------
def test_many_to_many(client):
    ev = client.get("/api/events/1/artists").get_json()
    assert {a["id"] for a in ev["artists"]} == {1, 2}
    art = client.get("/api/artists/2/events").get_json()
    assert {e["id"] for e in art["events"]} >= {1, 2}
    # додати / видалити зв'язок
    assert client.post("/api/events/9/artists", json={"artist_id": 6}).status_code == 201
    assert client.post("/api/events/9/artists", json={"artist_id": 6}).status_code == 409
    assert 6 in {a["id"] for a in client.get("/api/events/9/artists").get_json()["artists"]}
    assert client.delete("/api/events/9/artists/6").status_code == 200
    assert client.delete("/api/events/9/artists/6").status_code == 404


# ---------- бізнес-логіка ----------
def test_ticket_purchase_flow(client):
    seat = client.get("/api/events/1/seats/available").get_json()["available_seats"][0]
    order = client.post("/api/orders", json={"customer_id": 2, "delivery_option_id": 1,
                                             "order_datetime": "2026-11-16 12:00:00"}).get_json()
    t = client.post("/api/tickets", json={"order_id": order["id"], "event_seat_id": seat["id"]})
    assert t.status_code == 201 and t.get_json()["ticket_code"].startswith("TKT-")
    assert client.get(f"/api/event-seats/{seat['id']}").get_json()["status"] == "sold"
    # те саме місце вдруге купити не можна
    again = client.post("/api/tickets", json={"order_id": order["id"], "event_seat_id": seat["id"]})
    assert again.status_code == 409
    # сума замовлення та оплата без вказання amount
    assert client.get(f"/api/orders/{order['id']}/summary").get_json()["total"] == seat["price"]
    p = client.post("/api/payments", json={"order_id": order["id"], "payment_method_id": 1, "status": "success"})
    assert p.status_code == 201 and p.get_json()["amount"] == seat["price"]
    # повернення квитка звільняє місце
    client.delete(f"/api/payments/{p.get_json()['id']}")
    assert client.delete(f"/api/tickets/{t.get_json()['id']}").status_code == 200
    assert client.get(f"/api/event-seats/{seat['id']}").get_json()["status"] == "available"
    client.delete(f"/api/orders/{order['id']}")
