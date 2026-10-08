import math
import sqlite3
import time
from contextlib import closing

from app.domain.services.sql_challenges import TABLES

FUNCTIONS = {"sum", "count", "min", "max", "avg", "coalesce", "ifnull", "round", "abs", "lower", "upper", "length", "substr", "trim"}


class SQLSandbox:
    def run(self, query, dataset):
        if not query.strip() or len(query) > 4000:
            return {"ok": False, "error": "query_limit"}
        with closing(sqlite3.connect(":memory:")) as connection:
            connection.execute("CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
            connection.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id INTEGER, total INTEGER, status TEXT)")
            connection.executemany("INSERT INTO customers VALUES (?, ?)", dataset["customers"])
            connection.executemany("INSERT INTO orders VALUES (?, ?, ?, ?)", dataset["orders"])
            connection.commit()
            for category, limit in ((sqlite3.SQLITE_LIMIT_LENGTH, 65536), (sqlite3.SQLITE_LIMIT_SQL_LENGTH, 4000),
                    (sqlite3.SQLITE_LIMIT_COLUMN, 32), (sqlite3.SQLITE_LIMIT_COMPOUND_SELECT, 10),
                    (sqlite3.SQLITE_LIMIT_EXPR_DEPTH, 30), (sqlite3.SQLITE_LIMIT_VDBE_OP, 10000),
                    (sqlite3.SQLITE_LIMIT_ATTACHED, 0), (sqlite3.SQLITE_LIMIT_FUNCTION_ARG, 8)):
                connection.setlimit(category, limit)
            connection.execute("PRAGMA query_only=ON")
            def authorize(action, first, second, database, trigger):
                if action == sqlite3.SQLITE_SELECT:
                    return sqlite3.SQLITE_OK
                if action == sqlite3.SQLITE_READ and database in {None, "main"} and first in TABLES:
                    return sqlite3.SQLITE_OK
                if action == sqlite3.SQLITE_FUNCTION and (second or "").casefold() in FUNCTIONS:
                    return sqlite3.SQLITE_OK
                return sqlite3.SQLITE_DENY
            deadline, ticks = time.monotonic() + 0.2, 0
            def progress():
                nonlocal ticks
                ticks += 1
                return ticks >= 1000 or time.monotonic() >= deadline
            connection.set_authorizer(authorize)
            connection.set_progress_handler(progress, 100)
            try:
                cursor = connection.execute(query)
                rows, size = [], 0
                for row in cursor:
                    for value in row:
                        if isinstance(value, bytes) or isinstance(value, float) and not math.isfinite(value):
                            return {"ok": False, "error": "unsupported_value"}
                        size += len(value.encode("utf-8")) if isinstance(value, str) else 32
                    if len(rows) >= 100 or size > 16384:
                        return {"ok": False, "error": "result_limit"}
                    rows.append(list(row))
                columns = [column[0].casefold() for column in cursor.description or []]
                return {"ok": True, "columns": columns, "rows": rows}
            except (sqlite3.Error, MemoryError, OverflowError):
                return {"ok": False, "error": "query_rejected"}
