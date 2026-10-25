"""The connection to Postgres."""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app import config

# The engine owns a pool of open connections that requests borrow and return.
engine = create_engine(
    config.DATABASE_URL,
    pool_size=5,  # connections kept open
    max_overflow=5,  # extra connections allowed under load
    pool_timeout=5,  # seconds a request waits for a free connection
    pool_pre_ping=True,  # test a connection before use, so a dead one is replaced
)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    """The parent of every table class."""


def get_session() -> Iterator[Session]:
    """Give a request its own database session, and close it afterwards."""
    with SessionLocal() as session:
        yield session
