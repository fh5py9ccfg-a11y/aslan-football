from __future__ import annotations

from dataclasses import dataclass
import re


_IMAGE_PATTERN = re.compile(
    r"^(?P<registry>[a-zA-Z0-9._:-]+)/(?P<repository>[a-zA-Z0-9._/-]+):(?P<tag>[a-zA-Z0-9._-]+)$"
)


@dataclass(frozen=True)
class ContainerImage:
    registry: str
    repository: str
    tag: str
    digest: str | None = None

    @property
    def reference(self) -> str:
        base = f"{self.registry}/{self.repository}:{self.tag}"
        return f"{base}@{self.digest}" if self.digest else base


class ContainerImageValidator:
    def parse(self, reference: str) -> ContainerImage:
        if "@sha256:" in reference:
            base, digest_value = reference.split("@", 1)
            digest = digest_value
        else:
            base = reference
            digest = None

        match = _IMAGE_PATTERN.match(base)
        if not match:
            raise ValueError("Geçersiz container image referansı")

        if digest is not None:
            if not digest.startswith("sha256:") or len(digest) != 71:
                raise ValueError("Geçersiz image digest")

        return ContainerImage(
            registry=match.group("registry"),
            repository=match.group("repository"),
            tag=match.group("tag"),
            digest=digest,
        )

    def require_immutable(self, image: ContainerImage) -> None:
        if image.tag == "latest":
            raise ValueError("Production image latest etiketi kullanamaz")
        if image.digest is None:
            raise ValueError("Production image digest ile sabitlenmelidir")
