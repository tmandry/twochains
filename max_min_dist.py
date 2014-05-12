import argparse
import csv
from itertools import chain, combinations
from partition import Partition, TrivialPartition
import numpy

class ExplicitPartition(Partition):
  @classmethod
  def from_list(cls, numbers):
    """Creates a trivial partition with a list of any elements."""
    return cls([frozenset(numbers)], 1, len(numbers))

  def __init__(self, parts, depth, num_elements):
    """Creates a partition from a set of sets."""
    self.__parts = parts
    self.depth = depth
    self.num_elements = num_elements

  def __len__(self):
    return self.num_elements

  def parts(self):
    return self.__parts

  # Returns whether a and b are split in this partition.
  def are_split(self, a, b):
    # Get first part that contains a or b
    part = next(part for part in self.__parts if a in part or b in part)
    if a in part and b in part: return False
    return True

  def all_splits(self):
    """Returns a generator for all possible single splits of this partiton."""
    for part in self.__parts:
      parts = self.__parts[:]
      parts.remove(part)
      for split in self.__part_splits(part):
        new_parts = parts[:]
        new_parts.append(split)
        new_parts.append(part - split)
        yield ExplicitPartition(new_parts, self.depth + 1, self.num_elements)

  @staticmethod
  def __part_splits(part):
    # Select enough subsets so that the remaining subsets are complements of a subset we select,
    # excluding the empty and full sets.
    subsets = chain.from_iterable(combinations(part, n) for n in range(1, len(part)))
    subsets = (frozenset(s) for s in subsets)
    # Canonicalize every subset. Each element in this set now uniquely defines a possible split.
    # TODO optimize somehow?
    splits = frozenset(frozenset(min(tuple(s), tuple(part - s))) for s in subsets)
    return splits

def chains(partition):
  """Generate all possible chains from a single starting partition."""
  # return (Chain(chain) for chain in cls.__all_from_partition(partition))
  return __chains(partition)

def __chains(partition):
  if partition.depth == len(partition):
    return [[partition]]
  else:
    sub_chains = chain.from_iterable(__chains(split) for split in partition.all_splits())
    return ([partition]+c for c in sub_chains)

def compute_max_min_dist():
  """Main script to compute the maximum minimum distance between all chains of length n."""

  # Setup

  numpy.set_printoptions(linewidth = 100)

  parser = argparse.ArgumentParser()
  parser.add_argument("-n", type=int, help="size of partitions (and chains) to use", default=4)
  parser.add_argument("--write-lengths", help="write lengths of each optimal path to a file",
                      action="store_true")
  parser.add_argument("--lengths-file", help="location to write lengths",
                      default="lengths.csv")
  args = parser.parse_args()

  # Analysis

  p = ExplicitPartition.from_list(range(1, args.n + 1))
  all_chains = list(chains(p))

  print p
  for split in p.all_splits(): print split
  print '\n'.join([str(c) for c in chains(p)])
  print "%d chains" % len(all_chains)

  # Populate adjacency matrix.
  m = len(all_chains)
  matrix = numpy.matrix(numpy.zeros(shape=(m,m)))
  for i in range(m):
    for j in range(m):
      if i == j:
        matrix[i,j] = 1
      else:
        num_diffs = sum(x != y for (x, y) in zip(all_chains[i], all_chains[j]))
        if num_diffs < 2:
          matrix[i,j] = 1

  print matrix

  if args.write_lengths:
    # Lengths holds the length, not including the first hop, of the optimal path between
    # any two chains i and j.
    lengths = numpy.matrix(numpy.zeros(shape=(m,m)))

  # Raise power of matrix until no entries are zero.
  base_matrix = matrix.copy()
  max_dist = 1
  remaining_zeros = numpy.isclose(matrix, 0)
  while remaining_zeros.any():
    if args.write_lengths:
      for i in range(m):
        for j in range(i, m):
          if remaining_zeros[i,j]:
            lengths[i,j] += 1

    matrix = matrix * base_matrix
    max_dist += 1

    remaining_zeros = numpy.isclose(matrix, 0)

  print matrix
  print
  print "Maximal minimum distance between two chains is %d" % max_dist

  if args.write_lengths:
    with open(args.lengths_file, 'wb') as f:
      writer = csv.writer(f)
      for i in range(m):
        for j in range(i, m):
          if i == j: continue
          chain1 = ' -> '.join(repr(p) for p in all_chains[i])
          chain2 = ' -> '.join(repr(p) for p in all_chains[j])
          writer.writerow([chain1, chain2, int(lengths[i,j] + 1)])

if __name__ == "__main__": compute_max_min_dist()
