"""Service-шар: валідація вхідних даних та бізнес-логіка поверх DAO."""
import typing
from dataclasses import MISSING, fields
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

from my_project.utils.errors import NotFoundError, ValidationError


class BaseService:
    def __init__(self, dao):
        self.dao = dao
        self.entity = dao.entity
        self.label = self.entity.__name__
        self.hints = typing.get_type_hints(self.entity)
        self.required = [f.name for f in fields(self.entity) if f.name != "id" and f.default is MISSING]
        self.writable = [f.name for f in fields(self.entity) if f.name != "id"]

    # ---------- валідація ----------
    def _coerce(self, name: str, value):
        hint = self.hints[name]
        if typing.get_origin(hint) is typing.Union:          # Optional[X] -> X
            hint = [a for a in typing.get_args(hint) if a is not type(None)][0]
        if value is None:
            return None
        if hint is int:
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValidationError(f"Field '{name}' must be an integer")
            return value
        if hint is str:
            if not isinstance(value, str) or (name in self.required and not value.strip()):
                raise ValidationError(f"Field '{name}' must be a non-empty string")
            return value
        if hint is Decimal:
            try:
                d = Decimal(str(value))
            except (InvalidOperation, ValueError):
                raise ValidationError(f"Field '{name}' must be a number")
            if d < 0:
                raise ValidationError(f"Field '{name}' must be >= 0")
            return d
        if hint is datetime:
            try:
                return datetime.fromisoformat(str(value).replace("T", " ")).strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                raise ValidationError(f"Field '{name}' must be a datetime 'YYYY-MM-DD HH:MM:SS'")
        return value

    def validate(self, data: dict, partial: bool = False) -> dict:
        if not isinstance(data, dict):
            raise ValidationError("JSON object expected in request body")
        unknown = [k for k in data if k not in self.writable]
        if unknown:
            raise ValidationError(f"Unknown or read-only fields: {', '.join(unknown)}")
        if not partial:
            missing = [r for r in self.required if data.get(r) is None]
            if missing:
                raise ValidationError(f"Missing required fields: {', '.join(missing)}")
        if partial and not data:
            raise ValidationError("Nothing to update")
        return {k: self._coerce(k, v) for k, v in data.items()}

    # ---------- CRUD ----------
    def get_all(self, limit: Optional[int] = None, offset: int = 0):
        return self.dao.find_all(limit, offset)

    def get_by_id(self, id_: int):
        obj = self.dao.find_by_id(id_)
        if obj is None:
            raise NotFoundError(f"{self.label} with id={id_} not found")
        return obj

    def get_by_parent(self, column: str, parent_id: int):
        """Дочірні записи за зовнішнім ключем (M:1)."""
        return self.dao.find_by(column, parent_id)

    def create(self, data: dict):
        clean = self.validate(data)
        new_id = self.dao.insert(clean)
        return self.get_by_id(new_id)

    def update(self, id_: int, data: dict, partial: bool = False):
        self.get_by_id(id_)
        clean = self.validate(data, partial)
        self.dao.update(id_, clean)
        return self.get_by_id(id_)

    def delete(self, id_: int):
        self.get_by_id(id_)
        self.dao.delete(id_)
