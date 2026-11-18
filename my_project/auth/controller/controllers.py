"""Controller-шар: приймає HTTP-запити, викликає сервіси, повертає DTO у JSON."""
from flask import jsonify, request

from my_project.auth.domain.dto import EntityDTO, ParentWithChildrenDTO
from my_project.utils.errors import ValidationError


def _json_body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a JSON object")
    return data


class CrudController:
    """Універсальний REST-контролер для CRUD-операцій однієї сутності."""

    def __init__(self, service, name: str):
        self.service = service
        self.name = name

    def list(self):
        limit = request.args.get("limit", type=int)
        offset = request.args.get("offset", default=0, type=int)
        return jsonify(EntityDTO.many(self.service.get_all(limit, offset))), 200

    def get(self, id_):
        return jsonify(EntityDTO.from_entity(self.service.get_by_id(id_))), 200

    def create(self):
        obj = self.service.create(_json_body())
        return jsonify(EntityDTO.from_entity(obj)), 201

    def replace(self, id_):
        obj = self.service.update(id_, _json_body(), partial=False)
        return jsonify(EntityDTO.from_entity(obj)), 200

    def patch(self, id_):
        obj = self.service.update(id_, _json_body(), partial=True)
        return jsonify(EntityDTO.from_entity(obj)), 200

    def delete(self, id_):
        self.service.delete(id_)
        return jsonify({"message": f"{self.name} {id_} deleted"}), 200


class RelationController:
    """Зв'язок M:1 з боку «один»: батьківський запис + усі його дочірні записи."""

    def __init__(self, parent_service, child_service, fk_column: str, children_name: str):
        self.parent_service = parent_service
        self.child_service = child_service
        self.fk_column = fk_column
        self.children_name = children_name

    def children(self, parent_id):
        parent = self.parent_service.get_by_id(parent_id)
        kids = self.child_service.get_by_parent(self.fk_column, parent_id)
        dto = ParentWithChildrenDTO(EntityDTO.from_entity(parent), self.children_name, EntityDTO.many(kids))
        return jsonify(dto.to_dict()), 200


class EventSeatController(CrudController):
    def available(self, event_id):
        """Вільні місця на подію."""
        self.service.event_service.get_by_id(event_id)
        seats = self.service.dao.find_available(event_id)
        return jsonify({"event_id": event_id, "available_seats": EntityDTO.many(seats), "count": len(seats)}), 200


class OrderController(CrudController):
    def summary(self, order_id):
        return jsonify(self.service.summary(order_id)), 200


class EventArtistController:
    """Контролер зв'язку M:N event <-> artist."""

    def __init__(self, service):
        self.service = service

    def list(self):
        return jsonify([{"event_id": l.event_id, "artist_id": l.artist_id} for l in self.service.get_all()]), 200

    def artists_of_event(self, event_id):
        return jsonify(self.service.artists_of_event(event_id)), 200

    def events_of_artist(self, artist_id):
        return jsonify(self.service.events_of_artist(artist_id)), 200

    def link(self, event_id):
        body = _json_body()
        self.service.link(event_id, body.get("artist_id"))
        return jsonify({"message": "linked", "event_id": event_id, "artist_id": body["artist_id"]}), 201

    def unlink(self, event_id, artist_id):
        self.service.unlink(event_id, artist_id)
        return jsonify({"message": "unlinked", "event_id": event_id, "artist_id": artist_id}), 200
