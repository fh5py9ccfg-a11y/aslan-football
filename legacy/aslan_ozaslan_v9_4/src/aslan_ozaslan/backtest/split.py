from dataclasses import dataclass

@dataclass(frozen=True)
class TimeSplit:
    train_indices: tuple[int, ...]
    test_indices: tuple[int, ...]

def expanding_time_splits(timestamps, *, minimum_train_size, test_size):
    if minimum_train_size <= 0 or test_size <= 0:
        raise ValueError("Boyutlar pozitif olmalıdır")
    if timestamps != sorted(timestamps):
        raise ValueError("Zaman damgaları artan sırada olmalıdır")
    splits = []
    start = minimum_train_size
    while start + test_size <= len(timestamps):
        splits.append(TimeSplit(tuple(range(start)), tuple(range(start, start+test_size))))
        start += test_size
    return splits
