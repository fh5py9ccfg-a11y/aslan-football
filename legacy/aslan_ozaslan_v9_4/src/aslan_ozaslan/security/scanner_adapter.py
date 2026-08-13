from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .supply_chain import DependencyFinding


@dataclass(frozen=True)
class ImageScanRequest:
    image_reference: str


@dataclass(frozen=True)
class ImageScanResult:
    scanner_name: str
    image_reference: str
    findings: tuple[DependencyFinding, ...]


class VulnerabilityScanner(Protocol):
    name: str

    def scan(self, request: ImageScanRequest) -> ImageScanResult:
        ...


class ScannerService:
    def __init__(self, scanner: VulnerabilityScanner):
        self.scanner = scanner

    def scan(self, image_reference: str) -> ImageScanResult:
        if "@sha256:" not in image_reference:
            raise ValueError("Image taraması digest ile sabitlenmiş referans gerektirir")
        result = self.scanner.scan(ImageScanRequest(image_reference))
        if result.scanner_name != self.scanner.name:
            raise ValueError("Scanner kimliği uyuşmuyor")
        if result.image_reference != image_reference:
            raise ValueError("Taranan image referansı uyuşmuyor")
        return result
