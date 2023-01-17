# Hashtables

In this assignment, we will implement a custom hashtable using various collision resolution strategies and analyze its performance. 
Recall that collision resolution strategies are divided into two categories: open addressing and chaining.
We will consider two different types of open addressing (linear probing and quadratic probing), 
as well as chaining using a linked list. 

Each implementation will inherit from a `HashTable` abstract base class defined in `hashtable.py`. 
The `__getitem__`, `__setitem__`, and `__delitem__` methods correspond to hashtable `Search`, `Insert`, and `Delete` operations, respectively. 
The hash table is resized whenever the `maximum_load_factor` is reached.

## Assignment
The `open_addressing.py` and `chaining.py` files contain methods that must be implemented to look up an element (`__getitem__`), insert or replace an element (`__setitem__`), and delete an item (`__delitem__`) in our custom hash table. Complete these three methods in both files.

In addition, you must compare the performance of each collision resolution strategy. Generate plots using the `benchmarks.py` file (see the [Benchmarking section](#benchmarking)) and provide an analysis of the results in the `analysis.md` file.

## Dependencies

Before getting started, install the necessary dependencies by running the following command:
```
python3 -m pip install -r requirements.txt
```

## Recommended Order of Implementation

You can choose to tackle `open_addressing.py` and `chaining.py` in any order, but `chaining.py` will likely be easier. Witin either file, we recommend that you implement `__getitem__` and `__setitem__` first, and confirm that they are working correctly with the tests. After this, you should implement `__delitem__`, which may require making modifications to the other two methods.

## Chaining

Please complete the `__getitem__`, `__setitem__`, and `__delitem__` methods of the `ChainingHashTable` class in `chaining.py`. 
We will rely on Python's `collections.deque` data structure, which is an implementation of a linked list.

The `maximum_load_factor` of a `ChainingHashTable` can technically exceed 1, but this may result in slow lookup and insertion times. 
Typically, this value is set to around 1, and the hashtable is resized (reconstructed with twice the capacity) whenever it is reached. 

## Open addressing

With open addressing, a collision is resolved by probing through a sequence of indices until an open slot is found. 
The `maximum_load_factor` must be less than 1, otherwise insertions can fail if there are no open slots.

### Generator functions

To implement open addressing, it is important to understand Python's 
[generator functions](https://inventwithpython.com/blog/2021/09/24/what-is-a-python-generator-implementing-your-own-range-function/).
A tutorial is included in this repository as a Jupyter notebook; 
open `generator_tutorial.ipynb` in an appropriate editor such as PyCharm or VS Code to follow the tutorial. 

### Base class

In `open_addressing.py`, there is an abstract base class named `OpenAddressingHashTable`. 
Please complete the `__getitem__`, `__setitem__`, and `__delitem__` logic here (which is the same for all hashtables which use open addressing). These operations must take care to keep the fields `_num_elements` and eventually `_num_tombstones` (see below) up to date, since this info is used to determine when the hashtable is resized. 

Every subclass of `OpenAddressingHashTable` must implement the `_generate_indices` method as a generator function which produces 
a sequence of indices beginning at the index of a collision; this is called a probing sequence.

If the probing sequence is infinite, it is guaranteed to repeat itself (cycle), as the number of indices is finite. 
A goal of the probing sequence is that it should always find an open slot if the hashtable is not too full.
In other words, we want to ensure that any cycles are sufficiently long that we will find an open slot before cycling.

### [Linear probing](https://en.wikipedia.org/wiki/Linear_probing)

Please complete the `_generate_indices` method for the `LinearProbingHashTable` class in `open_addressing.py`. 
The linear probing sequence should not fail unless the hashtable is completely full, 
as its only cycle should be of length `m`, where `m` is the number of slots in the table.

### [Quadratic probing](https://en.wikipedia.org/wiki/Quadratic_probing)

With quadratic probing, it is easy to run into short cycles. 
For example, the sequence given on Wikipedia is `H + i^2`, where `H` is the original hash index, i.e.
`H, H + 1, H + 4, H + 9, ...`. Taken mod `m`, this can cycle very quickly: without exploring much of the table:
```ipython
 In [1]: def naive_quadratic_probe(start_index, capacity):
             count = 0
             while True:
                 yield (start_index + (count*count)) % capacity
                 count += 1

 In [2]: take(12, naive_quadratic_probe(start_index=6, capacity=8))
Out [2]: [6, 7, 2, 7, 6, 7, 2, 7, 6, 7, 2, 7]
```

To avoid short cycles, use the formula `H + (i^2 + i)/2`. This results in the sequence:
`H, H + 1, H + 3, H + 6, ...`. 
Prove to yourself that the numerator is always even, thus these values are always integers.

Please complete the `_generate_indices` method for the `QuadraticProbingHashTable` class in `open_addressing.py`.

### Deletion in open addressing hashtables

Implementing Delete for open addressing hashtables requires some careful consideration. You cannot simply
replace the deleted value with a blank slot, as it is possible future calls to the Search operator will 
fail to find their target key. Instead, we need a special value that represents a deleted key. This value
is called a tombstone.

When future calls to Search encounter a tombstone in the probe, they will pass over it as if they had seen a value (since it
is possible a value was there when the search key was inserted).

When future calls to Insert encounter a tombstone in the probe sequence, they are free to replace it with a new key value pair. **However, this only applies if the key is not already in the hashtable.** As a result, you should continue probing when you see a tombstone in order to determine if the key is already present. If it is not, overwrite the first tombstone you saw.

When any operation changes the number of tombstones, it needs to update `_num_tombstones`. Note that a tombstone does not count as an element, so it is not included in `_num_elements`.

Note - to prevent hashtables that fill up with tombstones from enountering infinite loops while probing, tombstones count towards
the load factor in our code. When the hashtable is resized, all tombstones are deleted.

## Testing

Several unit tests are provided for each class in `test_hashtables.py`.
You can run them all at onces with `python3 -m pytest`.

To focus on a particular class, pass a keyword expression: 
`python3 -m pytest -k LinearProbing` will only run tests for the `LinearProbingHashTable` class.

After completing the three different `HashTable` implementations, all test cases should pass.

## Benchmarking

Use the benchmarks in `benchmarks.py` to compare all three of your hashtable implementations as well as Python's built-in 
[dictionary](https://docs.python.org/3/tutorial/datastructures.html#dictionaries) class (`dict`).
Run `benchmarks.py`, and view the created plots in the `plots/` directory.
Choose a range of different values for the `maximum_load_factor` for each implementation.

`benchmarks.py` can be run with custom arguments to generate plots for hash tables with different parameters. Run the following command to view all the available options:
```
python3 benchmarks.py -h
```

Create the following plots comparing the various hashtables:
- Time taken to insert 1 million pairs (with no duplicate keys)
- Time taken to insert 1 million pairs (with duplicate keys)
- Time taken to look up 1 million pairs
- Time taken to delete 1 million pairs
- Memory used to store 1 million pairs (with no duplicate keys)

Note that `benchmarks.py` may take a minute or so to complete each trial.

Make sure to repeat the experiment multiple times with the `-r` command line argument to reduce the variance of your measurements.
All available command line arguments can be viewed with `python benchmarks.py --help` 

Once you are done plotting, write a short analysis of the results in `analysis.md`. 

