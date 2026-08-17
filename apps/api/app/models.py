from sqlalchemy import String, Integer, Text, DateTime, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class MatchEventModel(Base):
    __tablename__ = "match_events"
    __table_args__ = (
        UniqueConstraint(
            "fixture_id",
            "sequence",
            name="uq_match_events_fixture_sequence",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fixture_id: Mapped[str] = mapped_column(String(120), index=True)
    sequence: Mapped[int] = mapped_column(Integer)
    event_type: Mapped[str] = mapped_column(String(40))
    minute: Mapped[int] = mapped_column(Integer)
    team: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

class OutboxMessageModel(Base):
    __tablename__ = "outbox_messages"

    message_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    aggregate_id: Mapped[str] = mapped_column(String(120), index=True)
    topic: Mapped[str] = mapped_column(String(160), index=True)
    payload_json: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="PENDING", index=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    available_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

class MessageReceiptModel(Base):
    __tablename__ = "message_receipts"

    consumer_group: Mapped[str] = mapped_column(
        String(120),
        primary_key=True,
    )
    message_id: Mapped[str] = mapped_column(
        String(160),
        primary_key=True,
    )
    processed_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
class FixtureModel(Base):
    __tablename__ = "fixtures"
    __table_args__ = (
        UniqueConstraint(
            "provider",
            "provider_fixture_id",
            name="uq_fixtures_provider_fixture",
        ),
    )

    fixture_id: Mapped[str] = mapped_column(
        String(160),
        primary_key=True,
    )
    provider: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="sportmonks",
    )
    provider_fixture_id: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )
    league_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    home_team: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    away_team: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    kickoff_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="scheduled",
    )
    raw_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
