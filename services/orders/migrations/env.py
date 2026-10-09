"""Tells Alembic which database to change and what the tables should look like."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

from app import config as app_config
from app import models  # noqa: F401  (importing registers the tables on Base)
from app.db import Base

if context.config.config_file_name is not None:
    fileConfig(context.config.config_file_name)

# The tables as the code describes them, used when generating a new migration
target_metadata = Base.metadata


def run_migrations() -> None:
    engine = create_engine(app_config.DATABASE_URL)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


run_migrations()
