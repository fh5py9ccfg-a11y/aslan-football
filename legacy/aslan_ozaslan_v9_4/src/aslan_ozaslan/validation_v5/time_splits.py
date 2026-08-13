from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class TimedSample:
    sample_id: str
    occurred_at: datetime

@dataclass(frozen=True)
class TimeSplit:
    train_ids: tuple[str, ...]
    validation_ids: tuple[str, ...]

class ExpandingWindowSplitter:
    def split(
        self,
        samples: list[TimedSample],
        *,
        minimum_train_size: int,
        validation_size: int,
        step_size: int | None = None,
    ) -> tuple[TimeSplit, ...]:
        if minimum_train_size <= 0 or validation_size <= 0:
            raise ValueError("Split boyutları pozitif olmalıdır")
        if step_size is None:
            step_size = validation_size
        if step_size <= 0:
            raise ValueError("step_size pozitif olmalıdır")
        if any(sample.occurred_at.tzinfo is None for sample in samples):
            raise ValueError("Tüm örnek zamanları timezone içermelidir")

        ordered = sorted(samples, key=lambda item: item.occurred_at)
        splits = []
        train_end = minimum_train_size

        while train_end + validation_size <= len(ordered):
            train = ordered[:train_end]
            validation = ordered[train_end:train_end + validation_size]
            splits.append(
                TimeSplit(
                    train_ids=tuple(item.sample_id for item in train),
                    validation_ids=tuple(item.sample_id for item in validation),
                )
            )
            train_end += step_size

        return tuple(splits)
