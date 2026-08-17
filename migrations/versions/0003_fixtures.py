from alembic import op
import sqlalchemy as sa


revision = "0003_fixtures"
down_revision = "0002_audit_events"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "fixtures",
        sa.Column("fixture_id", sa.String(length=160), primary_key=True),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("provider_fixture_id", sa.String(length=160), nullable=False),
        sa.Column("league_name", sa.String(length=255), nullable=True),
        sa.Column("home_team", sa.String(length=255), nullable=False),
        sa.Column("away_team", sa.String(length=255), nullable=False),
        sa.Column("kickoff_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("raw_json", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "provider",
            "provider_fixture_id",
            name="uq_fixtures_provider_fixture",
        ),
    )


def downgrade():
    op.drop_table("fixtures")
