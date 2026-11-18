"""Конкретні DAO для кожної таблиці + спеціальні запити."""
from my_project.auth.domain import entities as e
from my_project.auth.dao.base_dao import BaseDAO


class CountryDAO(BaseDAO):
    entity = e.Country


class CityDAO(BaseDAO):
    entity = e.City


class VenueDAO(BaseDAO):
    entity = e.Venue


class EventTypeDAO(BaseDAO):
    entity = e.EventType


class ArtistDAO(BaseDAO):
    entity = e.Artist


class EventDAO(BaseDAO):
    entity = e.Event


class SeatDAO(BaseDAO):
    entity = e.Seat


class EventSeatDAO(BaseDAO):
    entity = e.EventSeat

    def find_available(self, event_id: int):
        rows = self.db.fetch_all(
            "SELECT * FROM event_seat WHERE event_id = %s AND status = 'available' ORDER BY id", (event_id,))
        return [self._map(r) for r in rows]

    def lock_by_id(self, id_: int, cur):
        """SELECT ... FOR UPDATE — блокування місця на час покупки квитка."""
        row = self.db.fetch_one("SELECT * FROM event_seat WHERE id = %s FOR UPDATE", (id_,), cur)
        return self._map(row)

    def set_status(self, id_: int, status: str, cur=None):
        self.db.execute("UPDATE event_seat SET status = %s WHERE id = %s", (status, id_), cur)


class CustomerDAO(BaseDAO):
    entity = e.Customer


class DeliveryOptionDAO(BaseDAO):
    entity = e.DeliveryOption


class PaymentMethodDAO(BaseDAO):
    entity = e.PaymentMethod


class OrderDAO(BaseDAO):
    entity = e.Order

    def totals(self, order_id: int) -> dict:
        """Суми по замовленню: квитки на події, транспортні квитки, доставка, сплачено."""
        row = self.db.fetch_one("""
            SELECT
              (SELECT COUNT(*) FROM ticket WHERE order_id = o.id) AS ticket_count,
              (SELECT COUNT(*) FROM transport_ticket WHERE order_id = o.id) AS transport_ticket_count,
              COALESCE((SELECT SUM(es.price) FROM ticket t JOIN event_seat es ON es.id = t.event_seat_id
                        WHERE t.order_id = o.id), 0) AS tickets_total,
              COALESCE((SELECT SUM(price) FROM transport_ticket WHERE order_id = o.id), 0) AS transport_total,
              d.price AS delivery_price,
              COALESCE((SELECT SUM(amount) FROM payment WHERE order_id = o.id AND status = 'success'), 0) AS paid_total
            FROM orders o JOIN delivery_option d ON d.id = o.delivery_option_id
            WHERE o.id = %s""", (order_id,))
        return row


class TicketDAO(BaseDAO):
    entity = e.Ticket


class TransportRouteDAO(BaseDAO):
    entity = e.TransportRoute


class TransportTicketDAO(BaseDAO):
    entity = e.TransportTicket


class PaymentDAO(BaseDAO):
    entity = e.Payment


class EventArtistDAO:
    """DAO стикувальної таблиці event_artist (M:N) зі складеним ключем."""

    def __init__(self, db):
        self.db = db

    def find_all(self):
        rows = self.db.fetch_all("SELECT event_id, artist_id FROM event_artist ORDER BY event_id, artist_id")
        return [e.EventArtist(**r) for r in rows]

    def exists(self, event_id: int, artist_id: int) -> bool:
        return self.db.fetch_one(
            "SELECT 1 AS x FROM event_artist WHERE event_id = %s AND artist_id = %s", (event_id, artist_id)) is not None

    def link(self, event_id: int, artist_id: int):
        self.db.execute("INSERT INTO event_artist (event_id, artist_id) VALUES (%s, %s)", (event_id, artist_id))

    def unlink(self, event_id: int, artist_id: int) -> int:
        _, n = self.db.execute("DELETE FROM event_artist WHERE event_id = %s AND artist_id = %s", (event_id, artist_id))
        return n

    def find_artists_by_event(self, event_id: int):
        rows = self.db.fetch_all(
            "SELECT a.* FROM artist a JOIN event_artist ea ON ea.artist_id = a.id "
            "WHERE ea.event_id = %s ORDER BY a.id", (event_id,))
        return [e.Artist(**r) for r in rows]

    def find_events_by_artist(self, artist_id: int):
        rows = self.db.fetch_all(
            "SELECT ev.* FROM event ev JOIN event_artist ea ON ea.event_id = ev.id "
            "WHERE ea.artist_id = %s ORDER BY ev.start_datetime", (artist_id,))
        return [e.Event(**r) for r in rows]
