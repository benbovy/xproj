from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import TypeVar

K = TypeVar("K")
V = TypeVar("V")


class Frozen(Mapping[K, V]):
    """Wrapper around an object implementing the mapping interface to make it
    immutable. If you really want to modify the mapping, the mutable version is
    saved under the `mapping` attribute.
    """

    __slots__ = ("mapping",)

    def __init__(self, mapping: Mapping[K, V]):
        self.mapping = mapping

    def __getitem__(self, key: K) -> V:
        return self.mapping[key]

    def __iter__(self) -> Iterator[K]:
        return iter(self.mapping)

    def __len__(self) -> int:
        return len(self.mapping)

    def __contains__(self, key: object) -> bool:
        return key in self.mapping

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.mapping!r})"


def FrozenDict(*args, **kwargs) -> Frozen:
    return Frozen(dict(*args, **kwargs))
