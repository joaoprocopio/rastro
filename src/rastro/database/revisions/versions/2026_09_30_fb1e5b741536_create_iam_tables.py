"""create iam tables

Revision ID: fb1e5b741536
Revises:
Create Date: 2026-09-30 19:54:52.481940

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "fb1e5b741536"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "iam_identity",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("display_name", sa.String(length=320), nullable=False),
        sa.Column(
            "date_joined",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_iam_identity")),
        sa.UniqueConstraint("email", name=op.f("uq_iam_identity_email")),
    )
    op.create_table(
        "iam_session",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("token_digest", sa.LargeBinary(length=32), nullable=False),
        sa.Column("identity_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["identity_id"],
            ["iam_identity.id"],
            name=op.f("fk_iam_session_identity_id_iam_identity"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_iam_session")),
        sa.UniqueConstraint("token_digest", name=op.f("uq_iam_session_token_digest")),
    )
    op.create_index(
        op.f("ix_iam_session_identity_id"), "iam_session", ["identity_id"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_iam_session_identity_id"), table_name="iam_session")
    op.drop_table("iam_session")
    op.drop_table("iam_identity")
