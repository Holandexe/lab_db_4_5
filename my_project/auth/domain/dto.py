"""DTO (Data Transfer Object): об'єкти, які повертають контролери клієнту.
Перетворюють Decimal/datetime у JSON-сумісні типи і формують складені відповіді."""
from dataclasses import asdict, dataclass, field, fields, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any


def serialize(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.isoformat()
    return value


@dataclass
class EntityDTO:
    """Універсальний DTO однієї сутності."""
    data: dict

    @staticmethod
    def from_entity(entity) -> dict:
        return {f.name: serialize(getattr(entity, f.name)) for f in fields(entity)}

    @classmethod
    def many(cls, entities) -> list:
        return [cls.from_entity(e) for e in entities]


@dataclass
class ParentWithChildrenDTO:
    """Зв'язок M:1 з боку «один»: батьківський запис + список дочірніх (напр. країна + її міста)."""
    parent: dict
    children_name: str
    children: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"parent": self.parent, self.children_name: self.children, "count": len(self.children)}


@dataclass
class LinkedDTO:
    """Зв'язок M:N: запис + усі пов'язані записи другої таблиці (напр. подія + її артисти)."""
    owner: dict
    related_name: str
    related: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"owner": self.owner, self.related_name: self.related, "count": len(self.related)}


@dataclass
class OrderSummaryDTO:
    order: dict
    ticket_count: int
    transport_ticket_count: int
    tickets_total: float
    transport_total: float
    delivery_price: float
    total: float
    paid_total: float

    def to_dict(self) -> dict:
        return asdict(self)
