from __future__ import annotations

import itertools
import os
import time
import warnings
from collections import defaultdict
from typing import Any, Hashable, Iterable, Type
import argparse

import matplotlib.pyplot as plt
import numpy as np

from chaining import ChainingHashTable
from hashtable import HashTable
from open_addressing import LinearProbingHashTable, QuadraticProbingHashTable
from utils import deep_getsizeof

# Keep this below 3 million. Keys are generated as permutations of 10 characters.
KEY_COUNT = 1000000
CHAINING_LOAD_FACTOR = [0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2]
LINEAR_LOAD_FACTOR = [0.6, 0.65, 0.7, 0.75, 0.8, 0.85]
QUADRATIC_LOAD_FACTOR = [0.6, 0.65, 0.7, 0.75, 0.8, 0.85]


def benchmark(
    hashtable: dict | HashTable,
    test_keys: Iterable[Hashable],
    test_values: Iterable[Any],
    delete_keys: Iterable[Hashable],
    verbose: int = 0,
) -> tuple[float, float, float, float]:
    """Benchmarks the given hashtable using the provided keys and values.

    Parameters
    ----------
    hashtable : dict | HashTable
        Hashtable to benchmark.
    test_keys : Iterable[Hashable]
        Keys used in benchmark.
    test_values : Iterable[Any]
        Values used in benchmark.
    delete_keys : Iterable[Hashable]
        Permutation of insert keys to use in deletion.
    verbose : int = 0
        Verbose mode. Prints out useful information. Higher levels print more information

    Returns
    -------
    insertion_time_s : float
        Time taken to complete insertion benchmark.
    lookup_time_s : float
        Time taken to complete lookup benchmark.
    memory_usage_MB : float
        Memory usage in megabytes.

    Notes
    -----
    The function also checks that the hashtable is working successfully.
    An AssertionError is thrown if the hashtable has the wrong values in it, after all insertions.
    """
    hashtable_cls = hashtable.__class__
    hashtable_description = hashtable_cls.__name__
    if isinstance(hashtable, HashTable):
        hashtable_description += f"(maximum_load_factor={hashtable._maximum_load_factor})"

    kv_pairs = list(zip(test_keys, test_values))

    # Insert
    start_time = time.perf_counter()
    for key, value in kv_pairs:
        hashtable[key] = value
    insertion_time_s = time.perf_counter() - start_time
    if verbose > 2:
        print(f"{hashtable_description} completed insertion benchmark in {insertion_time_s:.2f} s")

    # Lookup

    # Generate answer_kv_pairs
    answer_kv_pairs = []
    extra_kv_pairs = []
    seen_keys = set()
    for key, value in reversed(kv_pairs):
        if key in seen_keys:
            extra_kv_pairs.append((key, value))
            continue
        seen_keys.add(key)
        answer_kv_pairs.append((key, value))

    start_time = time.perf_counter()

    # Iterate over answer_kv_pairs, and check correctness (admittedly has some overhead)
    for key, value in answer_kv_pairs:
        v = hashtable[key]
        assert v == value, f"Value {v!r} for key {key!r} did not match expected value {value!r}"

    # Iterate over extra pairs to keep runtime accurate in duplicate runs
    for key, value in extra_kv_pairs:
        v = hashtable[key]
        # no assert: v likely differs from value

    lookup_time_s = time.perf_counter() - start_time
    if verbose > 2:
        print(f"{hashtable_description} completed lookup benchmark in {lookup_time_s:.2f} s")

    # Memory
    memory = deep_getsizeof(hashtable)
    memory_usage_MB = memory / 1e6
    if verbose > 2:
        print(f"{hashtable_description} used {memory_usage_MB:.2f} MB")

    # Delete
    start_time = time.perf_counter()
    for key in delete_keys:
        del hashtable[key]
    deletion_time_s = time.perf_counter() - start_time
    if verbose > 2:
        print(f"{hashtable_description} completed deletion benchmark in {deletion_time_s:.2f} s")

    return insertion_time_s, lookup_time_s, memory_usage_MB, deletion_time_s


def plot_results(
    hashtable_cls: type,
    mlfs: list[float],
    results: dict[type, list[float]],
    error_bars: bool = False):
    """Plots averages and potentially error bars from a list of results for a specific hash table

    Parameters
    ----------
    hashtable_cls: str
        Name of the hashtable plotted.
    mlfs: list[float]
        Maximum load factors that we are plotting for.
    results: dict[float, list[float]]
        Timing and memory results that will be used in plotting. Due to multiple measurements, plot the average.
    error_bars: bool = False
        Whether to add error bars to the data points.
    """
    data_points = []
    errors = []
    for mlf in mlfs:
        # Compute mean and variance for repetitions
        data_points.append(np.mean(results[mlf]))
        errors.append(np.std(results[mlf]))
    if error_bars:
        plt.errorbar(mlfs, data_points, errors, label=hashtable_cls.__name__)
    else:
        plt.plot(mlfs, data_points, label=hashtable_cls.__name__)


def run_benchmarks(
    trial_name: str,
    N: int,
    repeats: int,
    maximum_load_factors: dict[type, list[float]],
    duplicate_keys: bool = False,
    plot_insert: bool = False,
    plot_lookup: bool = False,
    plot_memory: bool = False,
    plot_delete: bool = False,
    error_bars: bool = False,
    verbose: int = 0,
):
    """Runs benchmarks for hashtables with the provided maximum load factors.

    Prints benchmark results to standard output, and saves created plots to the `plots` directory.

    Parameters
    ----------
    trial_name: str
        A name for the trial. Used in the filenames of output plots.
    N: int
        Number of operations to be performed.
    repeats: int
        Number of repetitions to reduce the variance of results.
    maximum_load_factors: dict[Type, list[float]]
        Maximum load factors to be used by the custom hashtables.
    duplicate_keys: bool = False
        If True, keys are created with duplicates via a resampling process.
        The set of distinct keys will be approximately 63% as large as the key list.
        (1 - 1/e is about 63%)
    plot_insert: bool = False
        If True, a plot is generated with insert times.
    plot_lookup: bool = False
        If True, a plot is generated with lookup times.
    plot_memory: bool = False
        If True, a plot is generated with used memory.
    plot_delete: bool = False
        If True, a plot is generated with delete times.
    error_bars: bool = False
        If True, error bars around data points are added.
    verbose: int = 0
        Verbose mode. Prints out useful information. Higher levels print more information

    Notes
    -----
    plot_insert, plot_lookup, and plot_memory are NOT mutually exclusive.
    If a plot is turned off, its statistic will still be computed and printed.
    """

    # Make plots subdirectory (if it doesn't exist)
    try:
        os.mkdir("plots")
    except FileExistsError:
        pass

    # Ensure that load factors are sorted.
    all_load_factors: set[float] = set()
    for hashtable_cls, load_factors in maximum_load_factors.items():
        all_load_factors.update(load_factors)
        maximum_load_factors[hashtable_cls] = sorted(load_factors)
    # Add dict with all possible load factors for baseline comparison
    maximum_load_factors[dict] = sorted(all_load_factors)

    print(f'____Beginning trial "{trial_name}"____')

    # Generate keys and values.
    test_string = "abcdefghij"  # 3,628,800 possible permutations
    test_keys = list(map("".join, itertools.islice(itertools.permutations(test_string), N)))
    np.random.shuffle(test_keys)

    if duplicate_keys:
        # Resample with replacement to cause some duplicate keys.
        test_keys = np.random.choice(test_keys, len(test_keys), replace=True)
    delete_keys = list(set(test_keys))
    np.random.shuffle(delete_keys)

    test_values = np.random.random(size=len(test_keys))

    insert_results: dict[dict[float, list[float]]] = defaultdict(lambda: defaultdict(list))
    lookup_results: dict[dict[float, list[float]]] = defaultdict(lambda: defaultdict(list))
    memory_results: dict[dict[float, list[float]]] = defaultdict(lambda: defaultdict(list))
    delete_results: dict[dict[float, list[float]]] = defaultdict(lambda: defaultdict(list))

    # Perform Tests
    for hashtable_cls, load_factors in maximum_load_factors.items():
        if verbose == 1:
            print(f"Running benchmarks for {hashtable_cls.__name__}")
        for load_factor in load_factors:
            if verbose > 1:
                print(f"Running benchmarks for {hashtable_cls.__name__}(maximum_load_factor={load_factor})")
            for _ in range(repeats):
                if hashtable_cls == dict:
                    hashtable = hashtable_cls()
                else:
                    hashtable = hashtable_cls(maximum_load_factor=load_factor)

                insertion_time, lookup_time, memory_usage, delete_time = benchmark(hashtable, test_keys, test_values, delete_keys, verbose=verbose)
                insert_results[hashtable_cls][load_factor].append(insertion_time)
                lookup_results[hashtable_cls][load_factor].append(lookup_time)
                memory_results[hashtable_cls][load_factor].append(memory_usage)
                delete_results[hashtable_cls][load_factor].append(delete_time)

    # Plot Results

    info_str = ""
    if duplicate_keys:
        info_str += " with duplicates"

    with warnings.catch_warnings():
        # Suppress matplotlib warnings
        warnings.simplefilter("ignore")

        if plot_insert:
            plt.title(f"Insertion Time {info_str}\nRan with #keys = {N} for {repeats} repetitions")
            plt.xlabel("Maximum Load Factor")
            plt.ylabel("Time Elapsed (seconds)")

            for hashtable_cls, results in insert_results.items():
                plot_results(hashtable_cls, maximum_load_factors[hashtable_cls], results, error_bars=error_bars)

            plt.legend()
            plt.savefig(f"plots/{trial_name}_insert.png")
            plt.close()

        if plot_lookup:
            plt.title(f"Lookup Time {info_str}\nRan with #keys = {N} for {repeats} repetitions")
            plt.xlabel("Maximum Load Factor")
            plt.ylabel("Time Elapsed (seconds)")

            for hashtable_cls, results in lookup_results.items():
                plot_results(hashtable_cls, maximum_load_factors[hashtable_cls], results, error_bars=error_bars)

            plt.legend()
            plt.savefig(f"plots/{trial_name}_lookup.png")
            plt.close()

        if plot_memory:
            plt.title(f"Memory Usage {info_str}\nRan with #keys = {N} for {repeats} repetitions")
            plt.xlabel("Maximum Load Factor")
            plt.ylabel("Memory Used (MB)")

            for hashtable_cls, results in memory_results.items():
                plot_results(hashtable_cls, maximum_load_factors[hashtable_cls], results, error_bars=error_bars)

            plt.legend()
            plt.savefig(f"plots/{trial_name}_memory.png")
            plt.close()

        if plot_delete:
            plt.title(f"Delete Time {info_str}\nRan with #keys = {N} for {repeats} repetitions")
            plt.xlabel("Maximum Load Factor")
            plt.ylabel("Time Elapsed (seconds)")

            for hashtable_cls, results in delete_results.items():
                plot_results(hashtable_cls, maximum_load_factors[hashtable_cls], results, error_bars=error_bars)

            plt.legend()
            plt.savefig(f"plots/{trial_name}_delete.png")
            plt.close()


def parse_args():
    parser = argparse.ArgumentParser(description="Run benchmarks on hashing implementation")
    parser.add_argument("--name", type=str, default="example", help="Name of the benchmark. Used as a prefix for the plot names.")
    parser.add_argument("-N", type=int, default=KEY_COUNT, help="Number of keys to benchmark with")
    parser.add_argument("-r", "--repetitions", type=int, default=1, help="Number of times to repeat the experiment for lowering variance")
    parser.add_argument("--chainingLoadFactor", type=float, nargs="+", default=CHAINING_LOAD_FACTOR, help="Chaining hash table load factor")
    parser.add_argument("--linearLoadFactor", type=float, nargs="+", default=LINEAR_LOAD_FACTOR, help="Linear Probing hash table load factor")
    parser.add_argument("--quadraticLoadFactor", type=float, nargs="+", default=QUADRATIC_LOAD_FACTOR, help="Quadratic Probing hash table load factor")
    parser.add_argument("--duplicates", action="store_true", default=False, help="Enable duplicates")
    parser.add_argument("--noPlotInsert", action="store_true", default=False, help="Disable plotting insert times")
    parser.add_argument("--noPlotLookup", action="store_true", default=False, help="Disable plotting lookup times")
    parser.add_argument("--noPlotMemory", action="store_true", default=False, help="Disable plotting memory usage")
    parser.add_argument("--noPlotDelete", action="store_true", default=False, help="Disable plotting delete times")
    parser.add_argument("--errorBars", action="store_true", default=False, help="Plot Error bars around data points")
    parser.add_argument("-v", "--verbose", action="count", default=0, help="Verbose mode. Prints out useful information. Higher levels print more information.")
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    # TODO: Select and run benchmarks, then look at the figures in the plots/ directory.
    args = parse_args()

    # You can delete/change this if you want. It is just an example.
    maximum_load_factors = {
        # Chaining load factor may exceed 1.0
        ChainingHashTable: args.chainingLoadFactor,
        # Open addressing load factors must be less than 1.0
        LinearProbingHashTable: args.linearLoadFactor,
        QuadraticProbingHashTable: args.quadraticLoadFactor,
    }

    run_benchmarks(
        trial_name=args.name,
        N=args.N,
        repeats=args.repetitions,
        maximum_load_factors=maximum_load_factors,
        duplicate_keys=False,
        plot_insert=(not args.noPlotInsert),
        plot_lookup=(not args.noPlotLookup),
        plot_memory=(not args.noPlotMemory),
        plot_delete=(not args.noPlotDelete),
        error_bars=args.errorBars,
        verbose=args.verbose,
    )
