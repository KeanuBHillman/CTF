import threading

from sqlmodel import Session, SQLModel, create_engine

from . import models  # noqa: F401


class CtfDB:
    _engine = None
    _lock = threading.Lock()

    @classmethod
    def _ensure_engine(cls):
        with cls._lock:
            if cls._engine is None:
                path = "ctf.db"
                if not path.startswith("sqlite:///"):
                    path = f"sqlite:///{path}"

                names = [t.name for t in SQLModel.metadata.sorted_tables]
                assert len(names) == len(set(names)), "Duplicate table names detected"

                cls._engine = create_engine(path)
                SQLModel.metadata.create_all(cls._engine)

    @classmethod
    def session(cls) -> Session:
        cls._ensure_engine()
        return Session(cls._engine)
