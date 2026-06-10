"""Initial database schema.

Revision ID: 20260610_0001
Revises:
Create Date: 2026-06-10
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260610_0001"
down_revision = None
branch_labels = None
depends_on = None


risk_tolerance_enum = postgresql.ENUM(
    "conservative", "moderate", "aggressive", name="risk_tolerance_enum"
)
asset_type_enum = postgresql.ENUM("stock", "crypto", "etf", "bond", name="asset_type_enum")
asset_type_enum2 = postgresql.ENUM("stock", "crypto", "etf", "bond", name="asset_type_enum2")
transaction_type_enum = postgresql.ENUM("buy", "sell", name="transaction_type_enum")
watchlist_asset_type_enum = postgresql.ENUM(
    "stock", "crypto", "etf", "bond", name="watchlist_asset_type_enum"
)
chat_role_enum = postgresql.ENUM("user", "assistant", "system", name="chat_role_enum")


def upgrade() -> None:
    bind = op.get_bind()

    for enum in (
        risk_tolerance_enum,
        asset_type_enum,
        asset_type_enum2,
        transaction_type_enum,
        watchlist_asset_type_enum,
        chat_role_enum,
    ):
        enum.create(bind, checkfirst=True)

    sa.Table(
        "users",
        sa.MetaData(),
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(200)),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column("risk_tolerance", risk_tolerance_enum),
        sa.Column("investment_goals", sa.JSON()),
        sa.Column("preferences", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
    ).create(bind, checkfirst=True)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False, if_not_exists=True)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=False, if_not_exists=True)

    sa.Table(
        "portfolios",
        sa.MetaData(),
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("cash_balance", sa.Numeric(20, 8)),
        sa.Column("currency", sa.String(10)),
        sa.Column("is_default", sa.Boolean()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    ).create(bind, checkfirst=True)

    sa.Table(
        "holdings",
        sa.MetaData(),
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("portfolio_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("asset_type", asset_type_enum, nullable=False),
        sa.Column("quantity", sa.Numeric(20, 8), nullable=False),
        sa.Column("average_buy_price", sa.Numeric(20, 8), nullable=False),
        sa.Column("current_price", sa.Numeric(20, 8)),
        sa.Column("last_price_update", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    ).create(bind, checkfirst=True)
    op.create_index(op.f("ix_holdings_symbol"), "holdings", ["symbol"], unique=False, if_not_exists=True)

    sa.Table(
        "transactions",
        sa.MetaData(),
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("portfolio_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("asset_type", asset_type_enum2, nullable=False),
        sa.Column("transaction_type", transaction_type_enum, nullable=False),
        sa.Column("quantity", sa.Numeric(20, 8), nullable=False),
        sa.Column("price", sa.Numeric(20, 8), nullable=False),
        sa.Column("total_value", sa.Numeric(20, 8), nullable=False),
        sa.Column("fees", sa.Numeric(20, 8)),
        sa.Column("notes", sa.Text()),
        sa.Column("executed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    ).create(bind, checkfirst=True)
    op.create_index(op.f("ix_transactions_symbol"), "transactions", ["symbol"], unique=False, if_not_exists=True)

    sa.Table(
        "watchlists",
        sa.MetaData(),
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("asset_type", watchlist_asset_type_enum, nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("alert_price_above", sa.Numeric(20, 8)),
        sa.Column("alert_price_below", sa.Numeric(20, 8)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    ).create(bind, checkfirst=True)

    sa.Table(
        "chat_histories",
        sa.MetaData(),
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("session_id", sa.String(100), nullable=False),
        sa.Column("role", chat_role_enum, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON()),
        sa.Column("tokens_used", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    ).create(bind, checkfirst=True)
    op.create_index(op.f("ix_chat_histories_session_id"), "chat_histories", ["session_id"], unique=False, if_not_exists=True)

    sa.Table(
        "refresh_tokens",
        sa.MetaData(),
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_revoked", sa.Boolean()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("token_hash"),
    ).create(bind, checkfirst=True)

    sa.Table(
        "analysis_cache",
        sa.MetaData(),
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("cache_key", sa.String(500), nullable=False),
        sa.Column("analysis_type", sa.String(100), nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("cache_key"),
    ).create(bind, checkfirst=True)
    op.create_index(op.f("ix_analysis_cache_cache_key"), "analysis_cache", ["cache_key"], unique=False, if_not_exists=True)
    op.create_index(op.f("ix_analysis_cache_symbol"), "analysis_cache", ["symbol"], unique=False, if_not_exists=True)


def downgrade() -> None:
    bind = op.get_bind()
    for table in (
        "analysis_cache",
        "refresh_tokens",
        "chat_histories",
        "watchlists",
        "transactions",
        "holdings",
        "portfolios",
        "users",
    ):
        sa.Table(table, sa.MetaData()).drop(bind, checkfirst=True)

    for enum in (
        chat_role_enum,
        watchlist_asset_type_enum,
        transaction_type_enum,
        asset_type_enum2,
        asset_type_enum,
        risk_tolerance_enum,
    ):
        enum.drop(bind, checkfirst=True)
