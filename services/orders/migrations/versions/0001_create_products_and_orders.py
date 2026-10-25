"""Create the products and orders tables.

Revision ID: 0001
Revises:
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("price_paise", sa.Integer, nullable=False),
        sa.Column("merchant_id", sa.String(32), nullable=False),
    )
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("customer_email", sa.String(254), nullable=False),
        sa.Column("merchant_id", sa.String(32), nullable=False),
        sa.Column(
            "product_id", sa.Integer, sa.ForeignKey("products.id"), nullable=False
        ),
        sa.Column("quantity", sa.Integer, nullable=False),
        sa.Column("amount_paise", sa.Integer, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    # Listing a customer's orders filters on this column. Without the index,
    # every such request reads the whole table.
    op.create_index("ix_orders_customer_email", "orders", ["customer_email"])


def downgrade() -> None:
    op.drop_index("ix_orders_customer_email", table_name="orders")
    op.drop_table("orders")
    op.drop_table("products")
