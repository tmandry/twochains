"""Defines the behavior common to all partitions and provides a trivial implementation.

This code is used in both chain_paths.py and max_min_dist.py."""

from itertools import chain

class Partition(object):
  """An abstract base class for partitions, which represent partitions of a set."""

  def __to_str(self, force_separators=False):
    """Convert a partition to a string, representing it as it is in the paper."""
    # Sort parts of partition so that any two partitions can be visually compared more easily.
    parts = sorted(list(part) for part in self.parts())

    if force_separators:
      separator = '.'
    else:
      separator = '.' if len(self) >= 10 else ''
    # The numbers in the parts are already sorted by the underlying set.
    return '|'.join(separator.join((str(n) for n in part)) for part in parts)
  def __str__(self):
    return self.__to_str()
  def __repr__(self):
    return self.__to_str(force_separators=True)

  def __eq__(self, other):
    return frozenset(self.parts()) == frozenset(other.parts())
  def __ne__(self, other):
    return frozenset(self.parts()) != frozenset(other.parts())

  def __len__(self):
    """Returns the number of elements in the underlying set, not the number of parts."""
    raise NotImplementedError

  def parts(self):
    raise NotImplementedError

  def splits(self):
    """Returns whether a given partition is the one that splits i and j in a chain."""
    raise NotImplementedError

class TrivialPartition(Partition):
  """A partition that contains only one part with all the elements, the integers from 1 to n."""

  def __init__(self, n):
    self.__n = n
    self.__parts = [frozenset(range(1, n+1))]

  def __len__(self):
    return self.__n

  def parts(self):
    return self.__parts

  def splits(self, i, j):
    return False
