"""Фабрика Flask-застосунку tickets_ua."""
import os

import pymysql
from flask import Flask, jsonify, render_template

from my_project.auth.route import build_blueprint
from my_project.utils.db import Database, load_config
from my_project.utils.errors import AppError

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def create_app(config_path: str = None) -> Flask:
    app = Flask(__name__, template_folder="ui/templates")
    app.json.ensure_ascii = False
    app.json.sort_keys = False

    cfg = load_config(config_path or os.path.join(ROOT, "config", "app.yml"))
    app.config["SERVER"] = cfg.get("server", {})
    app.config["DB"] = Database(cfg["database"])
    app.register_blueprint(build_blueprint(app.config["DB"]))

    @app.get("/")
    def index():
        rules = sorted(
            ((r.rule, ", ".join(sorted(r.methods - {"HEAD", "OPTIONS"}))) for r in app.url_map.iter_rules()
             if r.rule.startswith("/api")))
        return render_template("index.html", rules=rules)

    # ---- Обробка помилок -> JSON ----
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({"error": err.message}), err.status_code

    @app.errorhandler(pymysql.err.IntegrityError)
    def handle_integrity(err):
        code, msg = err.args[0], err.args[1]
        if code == 1062:
            text = "Duplicate value violates a unique constraint"
        elif code in (1451, 1452):
            text = "Foreign key constraint violation (referenced record missing or still in use)"
        elif code == 3819:
            text = "Value violates a CHECK constraint"
        else:
            text = "Integrity constraint violation"
        return jsonify({"error": text, "details": msg}), 409

    @app.errorhandler(pymysql.err.DataError)
    def handle_data_error(err):
        return jsonify({"error": "Invalid data value", "details": err.args[1]}), 400

    @app.errorhandler(pymysql.err.OperationalError)
    def handle_operational(err):
        return jsonify({"error": "Database is unavailable", "details": str(err.args[-1])}), 503

    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(405)
    def not_allowed(_):
        return jsonify({"error": "Method not allowed"}), 405

    return app
