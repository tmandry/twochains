from itertools import chain, combinations
from partition import Partition, TrivialPartition
import numpy

class ExplicitPartition(Partition):
  @classmethod
  def from_list(cls, numbers):
    return cls([frozenset(numbers)], 1, len(numbers))

  def __init__(self, parts, depth, num_elements):
    """Creates a partition from a set of sets."""
    self.parts = parts
    self.depth = depth
    self.num_elements = num_elements

  def __len__(self):
    return self.num_elements

  def all_parts(self):
    return self.parts

  # Returns whether a and b are split in this partition.
  def are_split(self, a, b):
    # Get first part that contains a or b
    part = next(part for part in self.parts if a in part or b in part)
    if a in part and b in part: return False
    return True

  def all_splits(self):
    """Returns a generator for all possible single splits of this partiton."""
    for part in self.parts:
      parts = self.parts[:]
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

  numpy.set_printoptions(linewidth = 100)

  p = ExplicitPartition.from_list(range(1, 4+1))
  print p
  print list(p.all_splits())

  all_chains = list(chains(p))
  print '\n'.join([str(c) for c in chains(p)])
  print "%d chains" % len(all_chains)

  m = len(all_chains)
  matrix = numpy.matrix(numpy.zeros(shape=(m,m)))

  for i in range(m):
    for j in range(m):
      if i == j:
        matrix[i,j] = 1
        continue
      diffs = sum(x != y for (x, y) in zip(all_chains[i], all_chains[j]))
      if diffs < 2: matrix[i,j] = 1

  print matrix

  base_matrix = matrix.copy()
  max_dist = 1

  while numpy.isclose(matrix, 0).any():
    matrix = matrix * base_matrix
    max_dist += 1

  print matrix
  print matrix.max()
  print
  print max_dist

if __name__ == "__main__": compute_max_min_dist()
