from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable, Iterator
from typing import Any, Generator, Hashable, MutableMapping, TypeVar

# Key type must be hashable
KT = TypeVar("KT", bound=Hashable)
# Value type can be anything
VT = TypeVar("VT")


class Blank(Iterator):
    """Placeholder representing an empty slot."""

    def __repr__(self) -> str:
        return "BLANK"

    def __iter__(self) -> Iterator:
        return self

    def __next__(self):
        raise StopIteration


class Tombstone():
    """Placeholder representing an empty slot that once held a value (open addressing only)"""

    def __repr__(self) -> str:
        return "TOMBSTONE"


# Use singleton instances of Blank and Tombstone as a sentinel value for empty slots
BLANK = Blank()
TOMBSTONE = Tombstone()


class HashTable(MutableMapping[KT, VT]):
    """Abstract base class for a hashtable."""

    def __init__(
        self,
        initial_capacity: int = 8,
        maximum_load_factor: float = 0.6,
    ):
        self._capacity = initial_capacity
        self._buckets: list[Any] = [BLANK] * initial_capacity
        self._num_elements = 0
        self._num_tombstones = 0

        self._maximum_load_factor = maximum_load_factor
        self._growth_factor = 2

    @property
    def _load_factor(self) -> float:
        return (self._num_elements + self._num_tombstones) / self._capacity

    def _resize(self):
        new_capacity = self._capacity * self._growth_factor
        new_table = self.__class__(
            initial_capacity=new_capacity,
            maximum_load_factor=self._maximum_load_factor,
        )
        for key, value in self.items():
            new_table[key] = value
        self.__dict__.update(new_table.__dict__)

    def __repr__(self) -> str:
        pairs = []
        for key, value in self.items():
            pairs.append(f"{key!r}: {value!r}")
        return "{" + ", ".join(sorted(pairs)) + "}"

    @abstractmethod
    def items(self) -> Iterable[tuple[KT, VT]]:
        ...

    def __len__(self) -> int:
        return self._num_elements

    def __iter__(self) -> Generator[KT, None, None]:
        """Creates an iterator over the keys of the HashTable.

        Returns
        -------
        iterator : Generator[KT, None, None]
            A generator object which emits the keys in the HashTable one by one.

        Notes
        -----
        Unlike the builtin dict_keyiterator, preservation of insertion order is not guaranteed.
        """
        return iter(key for key, _ in self.items())

    @abstractmethod
    def __getitem__(self, search_key: KT) -> VT:
        """Looks up the value associated with the given search key.

        Parameters
        ----------
        search_key : KT
            Key to look up in the HashTable.

        Returns
        -------
        value : VT
            Value associated with search_key.

        Raises
        ------
        KeyError
            If the search_key is not contained in the HashTable.
        """
        ...

    @abstractmethod
    def __setitem__(self, key: KT, value: VT):
        """Inserts the given key and value into the HashTable.

        Parameters
        ----------
        key : KT
            Key to insert.
        value : VT
            Value to insert.
        """
        ...

    @abstractmethod
    def __delitem__(self, key: KT):
        """Deletes the given key from the HashTable.

        Parameters
        ----------
        key : KT
            Key to delete.

        Raises
        ------
        KeyError
            If the search_key is not contained in the HashTable.
        """
        ...
