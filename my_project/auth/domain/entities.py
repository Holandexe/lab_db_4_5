"""Domain-шар: сутності, що відповідають таблицям БД tickets_ua.
Поля без значення за замовчуванням є обов'язковими при створенні (POST/PUT);
поля зі значенням None необов'язкові (або заповнюються значенням за замовчуванням у БД)."""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import ClassVar, Optional


@dataclass(kw_only=True)
class Entity:
    __table__: ClassVar[str] = ""
    id: Optional[int] = None


@dataclass(kw_only=True)
class Country(Entity):
    __table__: ClassVar[str] = "country"
    name: str
    iso_code: str


@dataclass(kw_only=True)
class City(Entity):
    __table__: ClassVar[str] = "city"
    country_id: int
    name: str


@dataclass(kw_only=True)
class Venue(Entity):
    __table__: ClassVar[str] = "venue"
    city_id: int
    name: str
    address: str
    capacity: int


@dataclass(kw_only=True)
class EventType(Entity):
    __table__: ClassVar[str] = "event_type"
    name: str


@dataclass(kw_only=True)
class Artist(Entity):
    __table__: ClassVar[str] = "artist"
    country_id: int
    name: str
    genre: str
    bio: Optional[str] = None


@dataclass(kw_only=True)
class Event(Entity):
    __table__: ClassVar[str] = "event"
    event_type_id: int
    venue_id: int
    title: str
    description: Optional[str] = None
    start_datetime: datetime
    status: Optional[str] = None  # scheduled | sold_out | cancelled | finished


@dataclass(kw_only=True)
class Seat(Entity):
    __table__: ClassVar[str] = "seat"
    venue_id: int
    sector: str
    row_no: int
    seat_no: int


@dataclass(kw_only=True)
class EventSeat(Entity):
    __table__: ClassVar[str] = "event_seat"
    event_id: int
    seat_id: int
    price: Decimal
    status: Optional[str] = None  # available | reserved | sold


@dataclass(kw_only=True)
class Customer(Entity):
    __table__: ClassVar[str] = "customer"
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    registered_at: Optional[datetime] = None


@dataclass(kw_only=True)
class DeliveryOption(Entity):
    __table__: ClassVar[str] = "delivery_option"
    name: str
    price: Optional[Decimal] = None
    description: Optional[str] = None


@dataclass(kw_only=True)
class PaymentMethod(Entity):
    __table__: ClassVar[str] = "payment_method"
    name: str


@dataclass(kw_only=True)
class Order(Entity):
    __table__: ClassVar[str] = "orders"
    customer_id: int
    delivery_option_id: int
    order_datetime: datetime
    status: Optional[str] = None  # new | paid | delivered | cancelled
    delivery_address: Optional[str] = None


@dataclass(kw_only=True)
class Ticket(Entity):
    __table__: ClassVar[str] = "ticket"
    order_id: int
    event_seat_id: int
    ticket_code: Optional[str] = None  # генерується автоматично


@dataclass(kw_only=True)
class TransportRoute(Entity):
    __table__: ClassVar[str] = "transport_route"
    transport_type: str  # train | plane | bus
    carrier: str
    route_number: str
    from_city_id: int
    to_city_id: int
    departure_datetime: datetime
    arrival_datetime: datetime
    base_price: Decimal


@dataclass(kw_only=True)
class TransportTicket(Entity):
    __table__: ClassVar[str] = "transport_ticket"
    order_id: int
    route_id: int
    passenger_name: str
    seat_label: str
    price: Decimal


@dataclass(kw_only=True)
class Payment(Entity):
    __table__: ClassVar[str] = "payment"
    order_id: int
    payment_method_id: int
    amount: Optional[Decimal] = None  # якщо не вказано — береться сума замовлення
    paid_at: Optional[datetime] = None
    status: Optional[str] = None  # success | pending | failed | refunded


@dataclass
class EventArtist:
    """Стикувальна таблиця M:N між event та artist (складений ключ)."""
    __table__: ClassVar[str] = "event_artist"
    event_id: int
    artist_id: int
