"""DAO-шар: усі SQL-запити до БД. BaseDAO реалізує CRUD для будь-якої сутності з first-key `id`."""
from dataclasses import fields
from typing import Optional

from my_project.utils.db import Database


class BaseDAO:
    entity = None  # клас сутності з domain

    def __init__(self, db: Database):
        self.db = db
        self.table = self.entity.__table__
        self.columns = [f.name for f in fields(self.entity)]
        self.writable = [c for c in self.columns if c != "id"]

    def _map(self, row):
        return self.entity(**row) if row else None

    def find_all(self, limit: Optional[int] = None, offset: int = 0, cur=None):
        sql = f"SELECT * FROM `{self.table}` ORDER BY id"
        params = []
        if limit is not None:
            sql += " LIMIT %s OFFSET %s"
            params = [limit, offset]
        return [self._map(r) for r in self.db.fetch_all(sql, params, cur)]

    def find_by_id(self, id_: int, cur=None):
        row = self.db.fetch_one(f"SELECT * FROM `{self.table}` WHERE id = %s", (id_,), cur)
        return self._map(row)

    def find_by(self, column: str, value, cur=None):
        """Вибірка за зовнішнім ключем (зв'язок M:1)."""
        if column not in self.columns:
            raise ValueError(f"Unknown column {column}")
        rows = self.db.fetch_all(f"SELECT * FROM `{self.table}` WHERE `{column}` = %s ORDER BY id", (value,), cur)
        return [self._map(r) for r in rows]

    def insert(self, data: dict, cur=None) -> int:
        cols = [c for c in self.writable if data.get(c) is not None]
        sql = (f"INSERT INTO `{self.table}` ({', '.join('`%s`' % c for c in cols)}) "
               f"VALUES ({', '.join(['%s'] * len(cols))})")
        last_id, _ = self.db.execute(sql, [data[c] for c in cols], cur)
        return last_id

    def update(self, id_: int, data: dict, cur=None) -> int:
        cols = [c for c in self.writable if c in data]
        if not cols:
            return 0
        sql = f"UPDATE `{self.table}` SET {', '.join('`%s` = %%s' % c for c in cols)} WHERE id = %s"
        _, count = self.db.execute(sql, [data[c] for c in cols] + [id_], cur)
        return count

    def delete(self, id_: int, cur=None) -> int:
        _, count = self.db.execute(f"DELETE FROM `{self.table}` WHERE id = %s", (id_,), cur)
        return count

    def exists(self, id_: int, cur=None) -> bool:
        return self.db.fetch_one(f"SELECT 1 AS x FROM `{self.table}` WHERE id = %s", (id_,), cur) is not None
