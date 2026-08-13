from alembic import op
import sqlalchemy as sa

revision = "0002_audit_events"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "audit_events",
        sa.Column(
            "id",
            sa.BigInteger(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "action",
            sa.String(length=120),
            nullable=False,
        ),
        sa.Column(
            "subject",
            sa.String(length=160),
            nullable=False,
        ),
        sa.Column(
            "resource",
            sa.String(length=200),
            nullable=False,
        ),
        sa.Column(
            "outcome",
            sa.String(length=40),
            nullable=False,
        ),
        sa.Column(
            "correlation_id",
            sa.String(length=160),
            nullable=False,
        ),
        sa.Column(
            "metadata_json",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_audit_events_subject",
        "audit_events",
        ["subject"],
    )
    op.create_index(
        "ix_audit_events_resource",
        "audit_events",
        ["resource"],
    )
    op.create_index(
        "ix_audit_events_outcome",
        "audit_events",
        ["outcome"],
    )
    op.create_index(
        "ix_audit_events_created_at",
        "audit_events",
        ["created_at"],
    )

def downgrade():
    op.drop_index(
        "ix_audit_events_created_at",
        table_name="audit_events",
    )
    op.drop_index(
        "ix_audit_events_outcome",
        table_name="audit_events",
    )
    op.drop_index(
        "ix_audit_events_resource",
        table_name="audit_events",
    )
    op.drop_index(
        "ix_audit_events_subject",
        table_name="audit_events",
    )
    op.drop_table("audit_events")
