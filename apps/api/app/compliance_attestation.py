from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json
import time


@dataclass(frozen=True)
class ComplianceAttestation:
    attestation_id: str
    change_id: str
    release_id: str
    key_id: str
    evidence_sha256: str
    compliance_sha256: str
    issued_by: str
    issued_at: int
    signature: str


@dataclass(frozen=True)
class AuditChainEntry:
    entry_id: str
    change_id: str
    sequence: int
    event_type: str
    payload_sha256: str
    previous_hash: str
    entry_hash: str
    recorded_at: int


class ComplianceAttestationError(RuntimeError):
    pass


class RedisComplianceAttestationRepository:
    def __init__(self, client, *, prefix='aslan:compliance-attestation', ttl_seconds=31_536_000):
        self.client = client
        self.prefix = prefix
        self.ttl_seconds = ttl_seconds

    def save_attestation(self, item: ComplianceAttestation) -> ComplianceAttestation:
        self.client.setex(self._attestation_key(item.attestation_id), self.ttl_seconds,
                          json.dumps(item.__dict__, ensure_ascii=False, separators=(',', ':')))
        self.client.setex(self._change_attestation_key(item.change_id), self.ttl_seconds, item.attestation_id)
        return item

    def get_attestation(self, attestation_id: str) -> ComplianceAttestation | None:
        payload = self.client.get(self._attestation_key(attestation_id))
        if payload is None: return None
        if isinstance(payload, bytes): payload = payload.decode('utf-8')
        return ComplianceAttestation(**json.loads(payload))

    def get_change_attestation(self, change_id: str) -> ComplianceAttestation | None:
        attestation_id = self.client.get(self._change_attestation_key(change_id))
        if attestation_id is None: return None
        if isinstance(attestation_id, bytes): attestation_id = attestation_id.decode('utf-8')
        return self.get_attestation(str(attestation_id))

    def append_entry(self, item: AuditChainEntry) -> AuditChainEntry:
        self.client.setex(self._entry_key(item.entry_id), self.ttl_seconds,
                          json.dumps(item.__dict__, ensure_ascii=False, separators=(',', ':')))
        self.client.sadd(self._chain_index(item.change_id), item.entry_id)
        return item

    def list_entries(self, change_id: str) -> tuple[AuditChainEntry, ...]:
        items=[]
        for entry_id in self.client.smembers(self._chain_index(change_id)):
            if isinstance(entry_id, bytes): entry_id=entry_id.decode('utf-8')
            payload=self.client.get(self._entry_key(str(entry_id)))
            if payload is None: continue
            if isinstance(payload, bytes): payload=payload.decode('utf-8')
            items.append(AuditChainEntry(**json.loads(payload)))
        items.sort(key=lambda x: x.sequence)
        return tuple(items)

    def _attestation_key(self, attestation_id): return f'{self.prefix}:attestation:{attestation_id}'
    def _change_attestation_key(self, change_id): return f'{self.prefix}:change-attestation:{change_id}'
    def _entry_key(self, entry_id): return f'{self.prefix}:entry:{entry_id}'
    def _chain_index(self, change_id): return f'{self.prefix}:chain:{change_id}'


class ComplianceAttestationService:
    def __init__(self, *, repository, change_management_service, signing_keys: dict[str, str], active_key_id: str):
        self.repository = repository
        self.change_management_service = change_management_service
        self.signing_keys = signing_keys
        self.active_key_id = active_key_id
        if active_key_id not in signing_keys:
            raise ValueError('Active attestation key bulunamadı')

    def attest(self, *, attestation_id: str, change_id: str, issued_by: str, now: int | None = None) -> ComplianceAttestation:
        evidence = self.change_management_service.repository.get_evidence(change_id)
        compliance = self.change_management_service.repository.get_compliance(change_id)
        change = self.change_management_service.repository.get_change(change_id)
        if change is None: raise KeyError('Change request bulunamadı')
        if evidence is None: raise ComplianceAttestationError('Release evidence bulunamadı')
        if compliance is None or not compliance.compliant:
            raise ComplianceAttestationError('Compliant snapshot olmadan attestation üretilemez')

        evidence_hash = self._sha(evidence.__dict__)
        compliance_payload = {**compliance.__dict__, 'gaps': list(compliance.gaps)}
        compliance_hash = self._sha(compliance_payload)
        issued_at = int(now if now is not None else time.time())
        unsigned = {
            'attestation_id': attestation_id,
            'change_id': change_id,
            'release_id': change.release_id,
            'key_id': self.active_key_id,
            'evidence_sha256': evidence_hash,
            'compliance_sha256': compliance_hash,
            'issued_by': issued_by,
            'issued_at': issued_at,
        }
        signature = self._sign(unsigned, self.active_key_id)
        item = ComplianceAttestation(**unsigned, signature=signature)
        self.repository.save_attestation(item)
        self.append_event(change_id=change_id, event_type='ATTESTATION_ISSUED', payload=item.__dict__, now=issued_at)
        return item

    def verify(self, *, attestation_id: str) -> dict:
        item = self.repository.get_attestation(attestation_id)
        if item is None: raise KeyError('Compliance attestation bulunamadı')
        if item.key_id not in self.signing_keys:
            return {'valid': False, 'reason': 'Signing key unavailable'}
        unsigned = {k: v for k, v in item.__dict__.items() if k != 'signature'}
        signature_valid = hmac.compare_digest(item.signature, self._sign(unsigned, item.key_id))
        evidence = self.change_management_service.repository.get_evidence(item.change_id)
        compliance = self.change_management_service.repository.get_compliance(item.change_id)
        evidence_valid = evidence is not None and self._sha(evidence.__dict__) == item.evidence_sha256
        compliance_payload = None if compliance is None else {**compliance.__dict__, 'gaps': list(compliance.gaps)}
        compliance_valid = compliance_payload is not None and self._sha(compliance_payload) == item.compliance_sha256
        return {
            'valid': signature_valid and evidence_valid and compliance_valid,
            'signature_valid': signature_valid,
            'evidence_valid': evidence_valid,
            'compliance_valid': compliance_valid,
            'attestation_id': item.attestation_id,
        }

    def append_event(self, *, change_id: str, event_type: str, payload: dict, entry_id: str | None = None, now: int | None = None) -> AuditChainEntry:
        entries = self.repository.list_entries(change_id)
        sequence = len(entries) + 1
        previous_hash = entries[-1].entry_hash if entries else '0' * 64
        recorded_at = int(now if now is not None else time.time())
        payload_hash = self._sha(payload)
        canonical = {
            'change_id': change_id,
            'sequence': sequence,
            'event_type': event_type,
            'payload_sha256': payload_hash,
            'previous_hash': previous_hash,
            'recorded_at': recorded_at,
        }
        entry_hash = self._sha(canonical)
        item = AuditChainEntry(
            entry_id=entry_id or f'{change_id}:{sequence}',
            entry_hash=entry_hash,
            **canonical,
        )
        return self.repository.append_entry(item)

    def verify_chain(self, *, change_id: str) -> dict:
        entries = self.repository.list_entries(change_id)
        previous = '0' * 64
        for expected_sequence, item in enumerate(entries, start=1):
            canonical = {
                'change_id': item.change_id,
                'sequence': item.sequence,
                'event_type': item.event_type,
                'payload_sha256': item.payload_sha256,
                'previous_hash': item.previous_hash,
                'recorded_at': item.recorded_at,
            }
            if item.sequence != expected_sequence or item.previous_hash != previous or self._sha(canonical) != item.entry_hash:
                return {'valid': False, 'entries': len(entries), 'broken_at': item.sequence}
            previous = item.entry_hash
        return {'valid': True, 'entries': len(entries), 'head': previous}

    def export_bundle(self, *, change_id: str) -> dict:
        change = self.change_management_service.repository.get_change(change_id)
        if change is None: raise KeyError('Change request bulunamadı')
        evidence = self.change_management_service.repository.get_evidence(change_id)
        compliance = self.change_management_service.repository.get_compliance(change_id)
        attestation = self.repository.get_change_attestation(change_id)
        chain = self.repository.list_entries(change_id)
        chain_verification = self.verify_chain(change_id=change_id)
        return {
            'change': {**change.__dict__, 'test_evidence': list(change.test_evidence)},
            'evidence': None if evidence is None else evidence.__dict__,
            'compliance': None if compliance is None else {**compliance.__dict__, 'gaps': list(compliance.gaps)},
            'attestation': None if attestation is None else attestation.__dict__,
            'audit_chain': [item.__dict__ for item in chain],
            'chain_verification': chain_verification,
        }

    def _sign(self, payload: dict, key_id: str) -> str:
        body = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')
        return hmac.new(self.signing_keys[key_id].encode('utf-8'), body, hashlib.sha256).hexdigest()

    @staticmethod
    def _sha(payload: dict) -> str:
        return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()
