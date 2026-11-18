"""Route-шар: зв'язує URL з контролерами та збирає залежності (DB -> DAO -> Service -> Controller)."""
from flask import Blueprint

from my_project.auth.controller.controllers import (
    CrudController, EventArtistController, EventSeatController, OrderController, RelationController)
from my_project.auth.dao import daos
from my_project.auth.service.services import (
    EventArtistService, OrderService, PaymentService, SimpleService, TicketService)


def _crud(bp: Blueprint, path: str, c: CrudController):
    """CRUD-маршрути: GET/POST /path, GET/PUT/PATCH/DELETE /path/<id>."""
    bp.add_url_rule(f"/{path}", f"{path}_list", c.list, methods=["GET"])
    bp.add_url_rule(f"/{path}", f"{path}_create", c.create, methods=["POST"])
    bp.add_url_rule(f"/{path}/<int:id_>", f"{path}_get", c.get, methods=["GET"])
    bp.add_url_rule(f"/{path}/<int:id_>", f"{path}_put", c.replace, methods=["PUT"])
    bp.add_url_rule(f"/{path}/<int:id_>", f"{path}_patch", c.patch, methods=["PATCH"])
    bp.add_url_rule(f"/{path}/<int:id_>", f"{path}_delete", c.delete, methods=["DELETE"])


def build_blueprint(db) -> Blueprint:
    bp = Blueprint("api", __name__, url_prefix="/api")

    # ---- DAO ----
    d = {n: getattr(daos, cls)(db) for n, cls in [
        ("country", "CountryDAO"), ("city", "CityDAO"), ("venue", "VenueDAO"), ("event_type", "EventTypeDAO"),
        ("artist", "ArtistDAO"), ("event", "EventDAO"), ("seat", "SeatDAO"), ("event_seat", "EventSeatDAO"),
        ("customer", "CustomerDAO"), ("delivery_option", "DeliveryOptionDAO"),
        ("payment_method", "PaymentMethodDAO"), ("order", "OrderDAO"), ("ticket", "TicketDAO"),
        ("transport_route", "TransportRouteDAO"), ("transport_ticket", "TransportTicketDAO"),
        ("payment", "PaymentDAO")]}
    link_dao = daos.EventArtistDAO(db)

    # ---- Services ----
    s = {n: SimpleService(d[n]) for n in [
        "country", "city", "venue", "event_type", "artist", "event", "seat", "customer",
        "delivery_option", "payment_method", "transport_route", "transport_ticket"]}
    s["event_seat"] = SimpleService(d["event_seat"])
    s["event_seat"].event_service = s["event"]
    s["order"] = OrderService(d["order"])
    s["ticket"] = TicketService(d["ticket"], d["event_seat"], d["order"])
    s["payment"] = PaymentService(d["payment"], s["order"])
    link_service = EventArtistService(link_dao, s["event"], s["artist"])

    # ---- CRUD ----
    for path, key in [("countries", "country"), ("cities", "city"), ("venues", "venue"),
                      ("event-types", "event_type"), ("artists", "artist"), ("events", "event"),
                      ("seats", "seat"), ("customers", "customer"), ("delivery-options", "delivery_option"),
                      ("payment-methods", "payment_method"), ("tickets", "ticket"),
                      ("transport-routes", "transport_route"), ("transport-tickets", "transport_ticket"),
                      ("payments", "payment")]:
        _crud(bp, path, CrudController(s[key], key))
    _crud(bp, "event-seats", EventSeatController(s["event_seat"], "event_seat"))
    _crud(bp, "orders", OrderController(s["order"], "order"))

    # ---- Спеціальні маршрути ----
    bp.add_url_rule("/events/<int:event_id>/seats/available", "event_seats_available",
                    EventSeatController(s["event_seat"], "event_seat").available, methods=["GET"])
    bp.add_url_rule("/orders/<int:order_id>/summary", "order_summary",
                    OrderController(s["order"], "order").summary, methods=["GET"])

    # ---- Зв'язки M:1 (для кожного батьківського запису — всі дочірні) ----
    for parent, child, fk, parent_key, child_key in [
        ("countries", "cities", "country_id", "country", "city"),
        ("countries", "artists", "country_id", "country", "artist"),
        ("cities", "venues", "city_id", "city", "venue"),
        ("venues", "events", "venue_id", "venue", "event"),
        ("venues", "seats", "venue_id", "venue", "seat"),
        ("event-types", "events", "event_type_id", "event_type", "event"),
        ("events", "seats", "event_id", "event", "event_seat"),
        ("customers", "orders", "customer_id", "customer", "order"),
        ("delivery-options", "orders", "delivery_option_id", "delivery_option", "order"),
        ("orders", "tickets", "order_id", "order", "ticket"),
        ("orders", "transport-tickets", "order_id", "order", "transport_ticket"),
        ("orders", "payments", "order_id", "order", "payment"),
        ("payment-methods", "payments", "payment_method_id", "payment_method", "payment"),
        ("transport-routes", "transport-tickets", "route_id", "transport_route", "transport_ticket"),
    ]:
        rc = RelationController(s[parent_key], s[child_key], fk, child.replace("-", "_"))
        bp.add_url_rule(f"/{parent}/<int:parent_id>/{child}", f"{parent}_{child}_children", rc.children, methods=["GET"])

    # ---- Зв'язок M:N (event_artist) ----
    ea = EventArtistController(link_service)
    bp.add_url_rule("/event-artists", "event_artists_list", ea.list, methods=["GET"])
    bp.add_url_rule("/events/<int:event_id>/artists", "event_artists_of_event", ea.artists_of_event, methods=["GET"])
    bp.add_url_rule("/events/<int:event_id>/artists", "event_artists_link", ea.link, methods=["POST"])
    bp.add_url_rule("/events/<int:event_id>/artists/<int:artist_id>", "event_artists_unlink", ea.unlink, methods=["DELETE"])
    bp.add_url_rule("/artists/<int:artist_id>/events", "event_artists_of_artist", ea.events_of_artist, methods=["GET"])
    return bp
