"""Робота з підключенням до MySQL (PyMySQL)."""
import os
from contextlib import contextmanager

import pymysql
import yaml
from pymysql.cursors import DictCursor


def load_config(path: str) -> dict:
    """Читає app.yml та накладає змінні оточення (DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)."""
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    db = cfg["database"]
    db["host"] = os.getenv("DB_HOST", db["host"])
    db["port"] = int(os.getenv("DB_PORT", db["port"]))
    db["user"] = os.getenv("DB_USER", db["user"])
    db["password"] = os.getenv("DB_PASSWORD", db["password"])
    db["name"] = os.getenv("DB_NAME", db["name"])
    return cfg


class Database:
    """Тонка обгортка над PyMySQL. Кожна операція виконується у власній транзакції,
    якщо ззовні не передано курсор (для багатокрокових бізнес-операцій)."""

    def __init__(self, cfg: dict):
        self.cfg = cfg

    def connect(self):
        return pymysql.connect(
            host=self.cfg["host"], port=self.cfg["port"],
            user=self.cfg["user"], password=self.cfg["password"],
            database=self.cfg["name"], charset=self.cfg.get("charset", "utf8mb4"),
            cursorclass=DictCursor, autocommit=False,
        )

    @contextmanager
    def cursor(self):
        """Транзакція: commit при успіху, rollback при будь-якій помилці."""
        conn = self.connect()
        try:
            with conn.cursor() as cur:
                yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _run(self, fn, cur):
        if cur is not None:
            return fn(cur)
        with self.cursor() as c:
            return fn(c)

    def fetch_all(self, sql, params=(), cur=None):
        def go(c):
            c.execute(sql, params)
            return list(c.fetchall())
        return self._run(go, cur)

    def fetch_one(self, sql, params=(), cur=None):
        def go(c):
            c.execute(sql, params)
            return c.fetchone()
        return self._run(go, cur)

    def execute(self, sql, params=(), cur=None):
        """Повертає (lastrowid, rowcount)."""
        def go(c):
            c.execute(sql, params)
            return c.lastrowid, c.rowcount
        return self._run(go, cur)
