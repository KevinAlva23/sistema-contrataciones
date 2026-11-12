"""Tablas iniciales"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "candidato",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("nombre", sa.String, nullable=False),
        sa.Column("email", sa.String, nullable=False),
        sa.Column("puesto", sa.String, nullable=False),
        sa.Column("telefono", sa.String, nullable=False),
        sa.Column("estado", sa.String, nullable=False, server_default="pendiente"),
        sa.Column("creado", sa.String, nullable=True),
        sa.Column("notas", sa.String, nullable=False, server_default=""),
    )
    op.create_table(
        "usuario",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("username", sa.String, nullable=False, unique=True),
        sa.Column("password_hash", sa.String, nullable=False),
        sa.Column("rol", sa.String, nullable=False, server_default="auditor"),
        sa.Column("activo", sa.Boolean, nullable=False, server_default=sa.true()),
    )
    op.create_table(
        "bitacora",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("fecha", sa.String, nullable=False),
        sa.Column("usuario", sa.String, nullable=False),
        sa.Column("accion", sa.String, nullable=False),
        sa.Column("detalle", sa.String, nullable=False, server_default=""),
    )


def downgrade():
    op.drop_table("bitacora")
    op.drop_table("usuario")
    op.drop_table("candidato")
