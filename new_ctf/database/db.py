"""
Database engine management.

CtfDB.get_engine() returns a shared SQLite engine.
Call CtfDB.init() on startup to create tables.
Use CtfDB.session() to get a plain Session (for scripts/tests).
"""

import threading
from typing import Generator

from sqlmodel import Session, SQLModel, create_engine

from . import models  # noqa: F401 — ensures all tables are registered before create_all


class CtfDB:
    _engine = None
    _lock = threading.Lock()

    @classmethod
    def get_engine(cls, db_url: str = "sqlite:///ctf.db"):
        with cls._lock:
            if cls._engine is None:
                cls._engine = create_engine(
                    db_url,
                    connect_args={"check_same_thread": False},
                )
        return cls._engine

    @classmethod
    def init(cls, db_url: str = "sqlite:///ctf.db") -> None:
        """Create all tables. Call once at application startup."""
        engine = cls.get_engine(db_url)
        SQLModel.metadata.create_all(engine)

    @classmethod
    def session(cls) -> Session:
        """Return a plain Session — useful in scripts. Caller is responsible for commit/close."""
        return Session(cls.get_engine())


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session per request."""
    with Session(CtfDB.get_engine()) as session:
        yield session
