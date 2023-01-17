from __future__ import annotations

import itertools
from collections import deque
from typing import Iterable, TypeVar

import pytest

from chaining import ChainingHashTable
from hashtable import BLANK, TOMBSTONE
from open_addressing import LinearProbingHashTable, QuadraticProbingHashTable

T = TypeVar("T")

# Note: The tests are designed using the fact that hash(x) = x for integers below some (large) upper bound.


def take(n: int, iterable: Iterable[T]) -> list[T]:
    "Return first n items of the iterable as a list"
    return list(itertools.islice(iterable, n))


class TestLinearProbing:
    def test_generate_indices(self):
        table = LinearProbingHashTable(initial_capacity=8)
        indices = take(10, table._generate_indices(6))

        expected = [6, 7, 0, 1, 2, 3, 4, 5, 6, 7]
        assert indices == expected

    def test_insertions(self):
        table = LinearProbingHashTable(initial_capacity=4, maximum_load_factor=0.8)

        # Test basic insertions
        table[2] = 100
        assert table._buckets == [BLANK, BLANK, (2, 100), BLANK]
        assert len(table) == 1
        table[3] = 101
        assert table._buckets == [BLANK, BLANK, (2, 100), (3, 101)]
        assert len(table) == 2

        # Test open addressing
        table[6] = 102
        assert table._buckets == [(6, 102), BLANK, (2, 100), (3, 101)]

        # Test overwrites
        table[2] = 90
        assert table._buckets == [(6, 102), BLANK, (2, 90), (3, 101)]
        assert len(table) == 3
        table[6] = 201
        assert table._buckets == [(6, 201), BLANK, (2, 90), (3, 101)]
        assert len(table) == 3

        # Test resize when maximum load factor is exceeded
        table[5] = 75
        assert len(table._buckets) == 8
        assert table._buckets == [BLANK, BLANK, (2, 90), (3, 101), BLANK, (5, 75), (6, 201), BLANK]

    def test_lookups(self):
        table = LinearProbingHashTable(initial_capacity=4, maximum_load_factor=0.8)

        table[2] = 100
        assert table._buckets == [BLANK, BLANK, (2, 100), BLANK]
        assert table[2] == 100

        table[3] = 101
        assert table._buckets == [BLANK, BLANK, (2, 100), (3, 101)]
        assert table[3] == 101

        table[6] = 102
        assert table._buckets == [(6, 102), BLANK, (2, 100), (3, 101)]
        assert table[6] == 102

        # Test missing key raises KeyError
        with pytest.raises(KeyError):
            _ = table[0]

    def test_delete(self):
        table = LinearProbingHashTable(initial_capacity=4, maximum_load_factor=0.8)

        table[2] = 100
        assert table._buckets == [BLANK, BLANK, (2, 100), BLANK]

        table[3] = 101
        assert table._buckets == [BLANK, BLANK, (2, 100), (3, 101)]

        table[6] = 102
        assert table._buckets == [(6, 102), BLANK, (2, 100), (3, 101)]

        del table[2]
        assert table._buckets == [(6, 102), BLANK, TOMBSTONE, (3, 101)]
        assert len(table) == 2
        assert table._num_tombstones == 1

        del table[3]
        assert table._buckets == [(6, 102), BLANK, TOMBSTONE, TOMBSTONE]
        assert len(table) == 1
        assert table._num_tombstones == 2

        # Test probing over tombstone
        with pytest.raises(KeyError):
            _ = table[10]

        assert table[6] == 102

        # Test insert into tombstone
        table[14] = 103
        assert table._buckets == [(6, 102), BLANK, (14, 103), TOMBSTONE]
        assert len(table) == 2
        assert table._num_tombstones == 1

        table[18] = 104
        assert table._buckets == [(6, 102), BLANK, (14, 103), (18, 104)]
        assert len(table) == 3
        assert table._num_tombstones == 0

        # Test missing key raises KeyError
        with pytest.raises(KeyError):
            del table[0]

    def test_iter(self):
        table = LinearProbingHashTable(initial_capacity=4, maximum_load_factor=0.8)

        table[2] = 100
        table[3] = 101
        assert list(table) == [2, 3]

    # This ought to be combined with the other tests, but has been temporarily
    # seperated out for ease of distribution.
    def test_delete_update(self):
        table = LinearProbingHashTable(initial_capacity=4, maximum_load_factor=0.8)
        table[1] = 100
        table[5] = 101
        table[9] = 102

        assert table._buckets == [BLANK, (1, 100), (5, 101), (9, 102)]
        
        del table[5]

        assert table._buckets == [BLANK, (1, 100), TOMBSTONE, (9, 102)]
        
        table[9] = 202

        # This is the important part! You must iterate over the TOMBSTONE to find
        # existing entry for 9
        assert table._buckets == [BLANK, (1, 100), TOMBSTONE, (9, 202)]
        # The wrong solution here is [BLANK, (1, 100), (9, 202), (9, 102)]

        table[13] = 103
        assert table._buckets == [BLANK, (1, 100), (13, 103), (9, 202)] 


class TestQuadraticProbing:
    def test_generate_indices(self):
        table = QuadraticProbingHashTable(initial_capacity=8)
        indices = take(15, table._generate_indices(6))

        expected = [6, 7, 1, 4, 0, 5, 3, 2, 2, 3, 5, 0, 4, 1, 7]
        assert indices == expected

    def test_insertions(self):
        table = QuadraticProbingHashTable(initial_capacity=8, maximum_load_factor=0.49)

        # Test basic insertions
        table[6] = 100
        assert table._buckets == [BLANK, BLANK, BLANK, BLANK, BLANK, BLANK, (6, 100), BLANK]
        assert len(table) == 1
        table[7] = 101
        assert table._buckets == [BLANK, BLANK, BLANK, BLANK, BLANK, BLANK, (6, 100), (7, 101)]
        assert len(table) == 2

        # Test open addressing
        table[14] = 102
        assert table._buckets == [BLANK, (14, 102), BLANK, BLANK, BLANK, BLANK, (6, 100), (7, 101)]
        assert len(table) == 3

        # Test overwrites
        table[6] = 90
        assert table._buckets == [BLANK, (14, 102), BLANK, BLANK, BLANK, BLANK, (6, 90), (7, 101)]
        assert len(table) == 3
        table[14] = 201
        assert table._buckets == [BLANK, (14, 201), BLANK, BLANK, BLANK, BLANK, (6, 90), (7, 101)]
        assert len(table) == 3

        # Test resize when maximum load factor is exceeded
        table[5] = 75
        assert len(table._buckets) == 16

    def test_lookups(self):
        table = QuadraticProbingHashTable(initial_capacity=8, maximum_load_factor=0.49)

        table[6] = 100
        assert table._buckets == [BLANK, BLANK, BLANK, BLANK, BLANK, BLANK, (6, 100), BLANK]
        assert table[6] == 100

        table[7] = 101
        assert table._buckets == [BLANK, BLANK, BLANK, BLANK, BLANK, BLANK, (6, 100), (7, 101)]
        assert table[7] == 101

        table[14] = 102
        assert table._buckets == [BLANK, (14, 102), BLANK, BLANK, BLANK, BLANK, (6, 100), (7, 101)]
        assert table[14] == 102

        # Test missing key raises KeyError
        with pytest.raises(KeyError):
            _ = table[0]

    def test_delete(self):
        # Also tests correct functionality relating to TOMBSTONE for other operations.
        table = QuadraticProbingHashTable(initial_capacity=8, maximum_load_factor=0.49)

        table[6] = 100
        assert table._buckets == [BLANK, BLANK, BLANK, BLANK, BLANK, BLANK, (6, 100), BLANK]

        table[7] = 101
        assert table._buckets == [BLANK, BLANK, BLANK, BLANK, BLANK, BLANK, (6, 100), (7, 101)]

        table[14] = 102
        assert table._buckets == [BLANK, (14, 102), BLANK, BLANK, BLANK, BLANK, (6, 100), (7, 101)]

        del table[6]
        assert table._buckets == [BLANK, (14, 102), BLANK, BLANK, BLANK, BLANK, TOMBSTONE, (7, 101)]
        assert len(table) == 2
        assert table._num_tombstones == 1

        del table[7]
        assert table._buckets == [BLANK, (14, 102), BLANK, BLANK, BLANK, BLANK, TOMBSTONE, TOMBSTONE]
        assert len(table) == 1
        assert table._num_tombstones == 2

        # Test probing over TOMBSTONE
        with pytest.raises(KeyError):
            _ = table[7]

        assert table[14] == 102

        # Test insert into TOMBSTONE
        table[22] = 103
        assert table._buckets == [BLANK, (14, 102), BLANK, BLANK, BLANK, BLANK, (22, 103), TOMBSTONE]
        assert len(table) == 2
        assert table._num_tombstones == 1

        table[30] = 104
        assert table._buckets == [BLANK, (14, 102), BLANK, BLANK, BLANK, BLANK, (22, 103), (30, 104)]
        assert len(table) == 3
        assert table._num_tombstones == 0

        # Test missing key raises KeyError
        with pytest.raises(KeyError):
            del table[0]

    def test_iter(self):
        table = QuadraticProbingHashTable(initial_capacity=4, maximum_load_factor=0.8)

        table[2] = 100
        table[3] = 101
        assert list(table) == [2, 3]

    # This ought to be combined with the other tests, but has been temporarily
    # seperated out for ease of distribution.
    def test_delete_update(self):
        table = QuadraticProbingHashTable(initial_capacity=4, maximum_load_factor=0.49)
        table[1] = 100
        table[9] = 101
        table[17] = 102

        assert table._buckets == [BLANK, (1, 100), (9, 101), BLANK, (17, 102), BLANK, BLANK, BLANK]

        del table[9]

        assert table._buckets == [BLANK, (1, 100), TOMBSTONE, BLANK, (17, 102), BLANK, BLANK, BLANK]

        table[17] = 202

        # This is the important part! You must iterate over the TOMBSTONE to find
        # existing entry for 17
        assert table._buckets == [BLANK, (1, 100), TOMBSTONE, BLANK, (17, 202), BLANK, BLANK, BLANK]
        # The wrong solution here is [BLANK, (1, 100), (17, 202), BLANK, (17, 102), BLANK, BLANK, BLANK]

        table[25] = 103
        assert table._buckets == [BLANK, (1, 100), (25, 103), BLANK, (17, 202), BLANK, BLANK, BLANK]


class TestChaining:
    def test_insertions(self):
        table = ChainingHashTable(initial_capacity=4, maximum_load_factor=0.9)

        # Test basic insertions
        table[2] = 100
        assert table._buckets == [BLANK, BLANK, deque([(2, 100)]), BLANK]
        assert len(table) == 1
        table[3] = 101
        assert table._buckets == [BLANK, BLANK, deque([(2, 100)]), deque([(3, 101)])]
        assert len(table) == 2

        # Test collisions
        table[6] = 200
        assert table._buckets == [BLANK, BLANK, deque([(2, 100), (6, 200)]), deque([(3, 101)])]
        assert len(table) == 3

        # Test overwrites
        table[2] = 90
        assert table._buckets == [BLANK, BLANK, deque([(2, 90), (6, 200)]), deque([(3, 101)])]
        assert len(table) == 3
        table[6] = 115
        assert table._buckets == [BLANK, BLANK, deque([(2, 90), (6, 115)]), deque([(3, 101)])]
        assert len(table) == 3

        # Test resize when maximum load factor is exceeded
        table[0] = 25
        assert len(table._buckets) == 8

    def test_lookups(self):
        table = ChainingHashTable(initial_capacity=4, maximum_load_factor=0.9)

        table[2] = 100
        assert table._buckets == [BLANK, BLANK, deque([(2, 100)]), BLANK]
        assert table[2] == 100

        table[3] = 101
        assert table._buckets == [BLANK, BLANK, deque([(2, 100)]), deque([(3, 101)])]
        assert table[3] == 101

        table[6] = 200
        assert table._buckets == [BLANK, BLANK, deque([(2, 100), (6, 200)]), deque([(3, 101)])]
        assert table[6] == 200

        # Test missing key raises KeyError
        with pytest.raises(KeyError):
            _ = table[0]

    def test_delete(self):
        table = ChainingHashTable(initial_capacity=4, maximum_load_factor=0.9) 

        table[2] = 100
        assert table._buckets == [BLANK, BLANK, deque([(2, 100)]), BLANK]
        assert table[2] == 100

        table[3] = 101
        assert table._buckets == [BLANK, BLANK, deque([(2, 100)]), deque([(3, 101)])]
        assert table[3] == 101

        table[6] = 200
        assert table._buckets == [BLANK, BLANK, deque([(2, 100), (6, 200)]), deque([(3, 101)])]
        assert table[6] == 200

        del table[6]
        assert table._buckets == [BLANK, BLANK, deque([(2, 100)]), deque([(3, 101)])]
        assert len(table) == 2

        # Test deleting last item in buck restores it to BLANK
        del table[2]
        assert table._buckets == [BLANK, BLANK, BLANK, deque([(3, 101)])]
        assert len(table) == 1

        # Test missing key raises KeyError
        with pytest.raises(KeyError):
            del table[0]


    def test_iter(self):
        table = ChainingHashTable(initial_capacity=4, maximum_load_factor=0.8)

        table[2] = 100
        table[3] = 101
        assert list(table) == [2, 3]
