import logging

from apps.api.app.outbox_transport import (
    LoggingOutboxTransport,
    build_outbox_transport,
)

def test_logging_transport_returns_receipt():
    transport = LoggingOutboxTransport(
        logging.getLogger("test")
    )
    receipt = transport.publish(
        event_id="e1",
        payload={"a": 1},
    )

    assert receipt.accepted is True
    assert receipt.event_id == "e1"
    assert receipt.transport == "logging"
    assert len(receipt.payload_sha256) == 64

def test_transport_factory_builds_logging():
    transport = build_outbox_transport(
        kind="logging",
        logger=logging.getLogger("test"),
    )
    assert transport.name == "logging"
