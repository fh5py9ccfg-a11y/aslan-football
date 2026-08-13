from __future__ import annotations
import json
from collections import defaultdict, deque
from pathlib import Path

from .domain import KnowledgeRelation

class FootballKnowledgeGraph:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path is not None else None
        self._edges = []
        if self.path and self.path.exists():
            self._load()

    def add(self, relation: KnowledgeRelation) -> None:
        relation.validate()
        key = (
            relation.source_id,
            relation.relation,
            relation.target_id,
        )
        for index, item in enumerate(self._edges):
            existing = (
                item.source_id,
                item.relation,
                item.target_id,
            )
            if existing == key:
                self._edges[index] = relation
                self._persist()
                return
        self._edges.append(relation)
        self._persist()

    def neighbors(
        self,
        node_id: str,
        *,
        relation: str | None = None,
    ) -> tuple[KnowledgeRelation, ...]:
        return tuple(sorted(
            (
                item for item in self._edges
                if item.source_id == node_id
                and (relation is None or item.relation == relation)
            ),
            key=lambda item: (-item.weight, item.target_id),
        ))

    def infer_paths(
        self,
        source_id: str,
        target_id: str,
        *,
        max_depth: int = 3,
    ) -> tuple[tuple[KnowledgeRelation, ...], ...]:
        if max_depth <= 0:
            raise ValueError("max_depth pozitif olmalıdır")

        adjacency = defaultdict(list)
        for edge in self._edges:
            adjacency[edge.source_id].append(edge)

        queue = deque([(source_id, tuple(), {source_id})])
        paths = []

        while queue:
            node, path, visited = queue.popleft()
            if len(path) >= max_depth:
                continue
            for edge in adjacency[node]:
                if edge.target_id in visited:
                    continue
                new_path = path + (edge,)
                if edge.target_id == target_id:
                    paths.append(new_path)
                else:
                    queue.append((
                        edge.target_id,
                        new_path,
                        visited | {edge.target_id},
                    ))

        return tuple(sorted(
            paths,
            key=lambda path: (
                -self.path_strength(path),
                len(path),
            ),
        ))

    def path_strength(
        self,
        path: tuple[KnowledgeRelation, ...],
    ) -> float:
        if not path:
            return 0.0
        strength = 1.0
        for edge in path:
            strength *= edge.weight
        return strength

    def _persist(self) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = [
            {
                "source_id": item.source_id,
                "relation": item.relation,
                "target_id": item.target_id,
                "weight": item.weight,
                "metadata": item.metadata,
            }
            for item in self._edges
        ]
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        temp.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temp.replace(self.path)

    def _load(self) -> None:
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        self._edges = [
            KnowledgeRelation(
                source_id=item["source_id"],
                relation=item["relation"],
                target_id=item["target_id"],
                weight=float(item["weight"]),
                metadata=dict(item.get("metadata") or {}),
            )
            for item in payload
        ]
