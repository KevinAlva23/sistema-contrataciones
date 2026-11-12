import os, sys
from alembic import context
from sqlmodel import SQLModel
from sqlalchemy import create_engine

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ["SOLO_MODELOS"] = "1"
import main  # noqa: registra los modelos

engine = create_engine(os.environ["DATABASE_URL"])
with engine.connect() as conn:
    context.configure(connection=conn, target_metadata=SQLModel.metadata)
    with context.begin_transaction():
        context.run_migrations()
