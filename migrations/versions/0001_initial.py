from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "match_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("fixture_id", sa.String(length=120), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("minute", sa.Integer(), nullable=False),
        sa.Column("team", sa.String(length=20), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "fixture_id",
            "sequence",
            name="uq_match_events_fixture_sequence",
        ),
    )
    op.create_index(
        "ix_match_events_fixture_id",
        "match_events",
        ["fixture_id"],
    )

    op.create_table(
        "outbox_messages",
        sa.Column("message_id", sa.String(length=160), primary_key=True),
        sa.Column("aggregate_id", sa.String(length=120), nullable=False),
        sa.Column("topic", sa.String(length=160), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column(
            "attempt_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column(
            "available_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_outbox_messages_status",
        "outbox_messages",
        ["status"],
    )
    op.create_index(
        "ix_outbox_messages_topic",
        "outbox_messages",
        ["topic"],
    )

    op.create_table(
        "message_receipts",
        sa.Column("consumer_group", sa.String(length=120), nullable=False),
        sa.Column("message_id", sa.String(length=160), nullable=False),
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("consumer_group", "message_id"),
    )

def downgrade():
    op.drop_table("message_receipts")
    op.drop_index("ix_outbox_messages_topic", table_name="outbox_messages")
    op.drop_index("ix_outbox_messages_status", table_name="outbox_messages")
    op.drop_table("outbox_messages")
    op.drop_index("ix_match_events_fixture_id", table_name="match_events")
    op.drop_table("match_events")
