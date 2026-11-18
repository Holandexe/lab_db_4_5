"""Конкретні сервіси з бізнес-логікою."""
import uuid
from decimal import Decimal

from my_project.auth.service.base_service import BaseService
from my_project.auth.domain.dto import LinkedDTO, EntityDTO, OrderSummaryDTO
from my_project.utils.errors import ConflictError, NotFoundError, ValidationError


class SimpleService(BaseService):
    """Сервіс без додаткової логіки (довідники тощо)."""


class TicketService(BaseService):
    """Купівля квитка: місце блокується, перевіряється статус і змінюється на 'sold' в одній транзакції."""

    def __init__(self, dao, event_seat_dao, order_dao):
        super().__init__(dao)
        self.event_seat_dao = event_seat_dao
        self.order_dao = order_dao

    def create(self, data: dict):
        clean = self.validate(data)
        if not self.order_dao.exists(clean["order_id"]):
            raise NotFoundError(f"Order with id={clean['order_id']} not found")
        with self.dao.db.cursor() as cur:
            seat = self.event_seat_dao.lock_by_id(clean["event_seat_id"], cur)
            if seat is None:
                raise NotFoundError(f"EventSeat with id={clean['event_seat_id']} not found")
            if seat.status != "available":
                raise ConflictError(f"Seat is not available (status='{seat.status}')")
            clean.setdefault("ticket_code", None)
            if not clean.get("ticket_code"):
                clean["ticket_code"] = "TKT-" + uuid.uuid4().hex[:10].upper()
            new_id = self.dao.insert(clean, cur)
            self.event_seat_dao.set_status(seat.id, "sold", cur)
        return self.get_by_id(new_id)

    def update(self, id_: int, data: dict, partial: bool = False):
        if "event_seat_id" in data:
            raise ValidationError("event_seat_id cannot be changed; delete the ticket and buy a new one")
        return super().update(id_, data, partial)

    def delete(self, id_: int):
        """Повернення квитка: місце знову стає доступним."""
        ticket = self.get_by_id(id_)
        with self.dao.db.cursor() as cur:
            self.dao.delete(id_, cur)
            self.event_seat_dao.set_status(ticket.event_seat_id, "available", cur)


class OrderService(BaseService):
    def summary(self, order_id: int) -> dict:
        order = self.get_by_id(order_id)
        t = self.dao.totals(order_id)
        tickets_total = float(t["tickets_total"])
        transport_total = float(t["transport_total"])
        delivery = float(t["delivery_price"])
        return OrderSummaryDTO(
            order=EntityDTO.from_entity(order),
            ticket_count=t["ticket_count"], transport_ticket_count=t["transport_ticket_count"],
            tickets_total=tickets_total, transport_total=transport_total, delivery_price=delivery,
            total=round(tickets_total + transport_total + delivery, 2),
            paid_total=float(t["paid_total"]),
        ).to_dict()


class PaymentService(BaseService):
    """Якщо сума оплати не вказана — вона дорівнює повній сумі замовлення."""

    def __init__(self, dao, order_service):
        super().__init__(dao)
        self.order_service = order_service

    def create(self, data: dict):
        if isinstance(data, dict) and data.get("amount") is None and data.get("order_id") is not None:
            order_id = data["order_id"]
            if not isinstance(order_id, int):
                raise ValidationError("Field 'order_id' must be an integer")
            data = {**data, "amount": self.order_service.summary(order_id)["total"]}
        return super().create(data)


class EventArtistService:
    """Зв'язок M:N між подіями та артистами."""

    def __init__(self, link_dao, event_service, artist_service):
        self.link_dao = link_dao
        self.event_service = event_service
        self.artist_service = artist_service

    def get_all(self):
        return self.link_dao.find_all()

    def artists_of_event(self, event_id: int) -> dict:
        event = self.event_service.get_by_id(event_id)
        artists = self.link_dao.find_artists_by_event(event_id)
        return LinkedDTO(EntityDTO.from_entity(event), "artists", EntityDTO.many(artists)).to_dict()

    def events_of_artist(self, artist_id: int) -> dict:
        artist = self.artist_service.get_by_id(artist_id)
        events = self.link_dao.find_events_by_artist(artist_id)
        return LinkedDTO(EntityDTO.from_entity(artist), "events", EntityDTO.many(events)).to_dict()

    def link(self, event_id: int, artist_id) -> None:
        if not isinstance(artist_id, int) or isinstance(artist_id, bool):
            raise ValidationError("Field 'artist_id' must be an integer")
        self.event_service.get_by_id(event_id)
        self.artist_service.get_by_id(artist_id)
        if self.link_dao.exists(event_id, artist_id):
            raise ConflictError("Artist is already linked to this event")
        self.link_dao.link(event_id, artist_id)

    def unlink(self, event_id: int, artist_id: int) -> None:
        if self.link_dao.unlink(event_id, artist_id) == 0:
            raise NotFoundError("Link between event and artist not found")
