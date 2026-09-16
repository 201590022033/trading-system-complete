"""DB-API transaction ownership shared by the existing repository adapters."""
from contextlib import contextmanager
from functools import wraps


class OwnedConnection:
    """Suppress leaf commits inside explicit scopes; nested scopes use savepoints."""
    def __init__(self, connection):
        self.raw = connection
        self.depth = 0

    def __getattr__(self, name):
        return getattr(self.raw, name)

    def commit(self):
        if not self.depth:
            self.raw.commit()

    def _statement(self, sql):
        cursor = self.raw.cursor()
        try: cursor.execute(sql)
        finally: cursor.close()

    @contextmanager
    def transaction(self):
        import sqlite3
        # Reserve the SQLite writer before read/modify/write work. Deferred
        # read locks cannot safely upgrade during a competing contribution.
        if not self.depth and isinstance(self.raw, sqlite3.Connection) and not self.raw.in_transaction:
            self._statement("BEGIN IMMEDIATE")
        name = f"repository_scope_{self.depth}"
        self._statement(f"SAVEPOINT {name}")
        self.depth += 1
        try:
            yield self
            self._statement(f"RELEASE SAVEPOINT {name}")
        except BaseException:
            self._statement(f"ROLLBACK TO SAVEPOINT {name}")
            self._statement(f"RELEASE SAVEPOINT {name}")
            if self.depth == 1:
                self.raw.rollback()
            raise
        else:
            if self.depth == 1:
                self.raw.commit()
        finally:
            self.depth -= 1


def atomic(method):
    @wraps(method)
    def wrapped(self, *args, **kwargs):
        with self.transaction():
            return method(self, *args, **kwargs)
    return wrapped
