"""Точка входу Back-End проєкту tickets_ua (Flask + MySQL)."""
from my_project import create_app

app = create_app()

if __name__ == "__main__":
    server = app.config["SERVER"]
    app.run(host=server.get("host", "127.0.0.1"),
            port=int(server.get("port", 5000)),
            debug=bool(server.get("debug", False)))
