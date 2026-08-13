from __future__ import annotations
from dataclasses import dataclass
import hashlib
import hmac
import json
import logging
import time
import urllib.request

from .transport_circuit_breaker import (
    CircuitOpen,
)

@dataclass(frozen=True)
class PublishReceipt:
    event_id: str
    transport: str
    destination: str
    accepted: bool
    external_id: str
    payload_sha256: str
    published_at: int

class OutboxTransport:
    name = "abstract"

    def publish(
        self,
        *,
        event_id: str,
        payload: dict,
    ) -> PublishReceipt:
        raise NotImplementedError

    @staticmethod
    def payload_digest(payload: dict) -> str:
        canonical = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()

class LoggingOutboxTransport(OutboxTransport):
    name = "logging"

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def publish(
        self,
        *,
        event_id: str,
        payload: dict,
    ) -> PublishReceipt:
        digest = self.payload_digest(payload)
        self.logger.info(
            "compensation_outbox event_id=%s digest=%s payload=%s",
            event_id,
            digest,
            payload,
        )
        return PublishReceipt(
            event_id=event_id,
            transport=self.name,
            destination="application-log",
            accepted=True,
            external_id=event_id,
            payload_sha256=digest,
            published_at=int(time.time()),
        )

class WebhookOutboxTransport(OutboxTransport):
    name = "webhook"

    def __init__(
        self,
        *,
        url: str,
        timeout_seconds: float = 5.0,
        authorization_header: str | None = None,
        signing_secret: str | None = None,
        circuit_breaker=None,
        clock=None,
    ):
        if not url:
            raise ValueError("Webhook URL gerekli")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds pozitif olmalıdır")
        if signing_secret is not None and len(signing_secret) < 16:
            raise ValueError(
                "Webhook signing secret en az 16 karakter olmalıdır"
            )
        self.url = url
        self.timeout_seconds = timeout_seconds
        self.authorization_header = authorization_header
        self.signing_secret = (
            signing_secret.encode("utf-8")
            if signing_secret
            else None
        )
        self.circuit_breaker = circuit_breaker
        self.clock = clock or time.time

    def publish(
        self,
        *,
        event_id: str,
        payload: dict,
    ) -> PublishReceipt:
        current = int(self.clock())
        if self.circuit_breaker is not None:
            self.circuit_breaker.before_call(
                now=current,
            )

        body = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        digest = hashlib.sha256(body).hexdigest()
        timestamp = str(current)

        headers = {
            "Content-Type": "application/json",
            "Idempotency-Key": event_id,
            "X-Event-Id": event_id,
            "X-Payload-SHA256": digest,
            "X-Webhook-Timestamp": timestamp,
        }
        if self.signing_secret is not None:
            signature = self._signature(
                timestamp=timestamp,
                event_id=event_id,
                body=body,
            )
            headers["X-Webhook-Signature"] = (
                f"sha256={signature}"
            )

        request = urllib.request.Request(
            self.url,
            data=body,
            method="POST",
            headers=headers,
        )
        if self.authorization_header:
            request.add_header(
                "Authorization",
                self.authorization_header,
            )

        try:
            with urllib.request.urlopen(
                request,
                timeout=self.timeout_seconds,
            ) as response:
                status = int(response.status)
                external_id = (
                    response.headers.get("X-Message-Id")
                    or response.headers.get("X-Request-Id")
                    or event_id
                )

            if status < 200 or status >= 300:
                raise RuntimeError(
                    f"Webhook publish başarısız: HTTP {status}"
                )

            if self.circuit_breaker is not None:
                self.circuit_breaker.record_success(
                    now=current,
                )

            return PublishReceipt(
                event_id=event_id,
                transport=self.name,
                destination=self.url,
                accepted=True,
                external_id=external_id,
                payload_sha256=digest,
                published_at=current,
            )
        except CircuitOpen:
            raise
        except Exception as exc:
            if self.circuit_breaker is not None:
                self.circuit_breaker.record_failure(
                    str(exc),
                    now=current,
                )
            raise

    def _signature(
        self,
        *,
        timestamp: str,
        event_id: str,
        body: bytes,
    ) -> str:
        message = (
            timestamp.encode("utf-8")
            + b"."
            + event_id.encode("utf-8")
            + b"."
            + body
        )
        return hmac.new(
            self.signing_secret,
            message,
            hashlib.sha256,
        ).hexdigest()

def build_outbox_transport(
    *,
    kind: str,
    logger: logging.Logger,
    webhook_url: str = "",
    webhook_timeout_seconds: float = 5.0,
    webhook_authorization_header: str | None = None,
    webhook_signing_secret: str | None = None,
    circuit_breaker=None,
) -> OutboxTransport:
    normalized = kind.strip().lower()
    if normalized == "logging":
        return LoggingOutboxTransport(logger)
    if normalized == "webhook":
        return WebhookOutboxTransport(
            url=webhook_url,
            timeout_seconds=webhook_timeout_seconds,
            authorization_header=webhook_authorization_header,
            signing_secret=webhook_signing_secret,
            circuit_breaker=circuit_breaker,
        )
    raise ValueError(
        f"Desteklenmeyen outbox transport: {kind}"
    )
