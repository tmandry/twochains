import argparse
import csv
import itertools
from partition import Partition, TrivialPartition
import random
import sys

random.seed(1234)

class Split(Partition):
  """A partition that is defined using a "parent" partiton and the split operation done on it.

  This eliminates redundancy in the representation and reduces the possibility for errors, like
  inconsistencies in a chain."""

  @classmethod
  def from_side(cls, parent, before, left):
    """Uses left to calculate right."""
    right = before - left
    return cls(parent, before, left, right)

  def __init__(self, parent, before, left, right):
    self.parent = parent
    self.before = before
    self.left = left
    self.right = right

  def __len__(self):
    return len(self.parent)

  def parts(self):
    # TODO cache result
    parts = self.parent.parts()[:]
    parts[parts.index(self.before)] = self.left
    parts.append(self.right)
    return parts

  def involves(self, num):
    """Returns whether num is involved in this split."""
    return num in self.before

  def splits(self, i, j):
    """Returns whether i and j are split apart in this split."""
    return (i in self.left and j in self.right) or (j in self.left and i in self.right)

class Chain(list):
  """A maximal chain of partitions.

  A chain is a list of partitions, so this class subclasses list."""

  @classmethod
  def random(cls, n):
    """Returns a randomized chain."""

    partitions = [TrivialPartition(n)]
    for _ in xrange(n-1):
      parent = partitions[-1]

      # Choose a random part to split
      before = random.choice([part for part in parent.parts() if len(part) > 1])
      before_list = list(before)

      # Split it randomly
      random.shuffle(before_list)
      idx = random.randrange(1, len(before_list))
      left, right = frozenset(before_list[0:idx]), frozenset(before_list[idx:])

      partitions.append(Split(parent, before, left, right))

    return cls(partitions)

  @classmethod
  def from_string(cls, s):
    raw_partitions = [p.split('|') for p in s.split(' -> ')]
    raw_partitions = [frozenset([frozenset([int(n) for n in part.split('.')]) for part in p]) for p in raw_partitions]

    n = len(list(raw_partitions[0])[0])
    partitions = [TrivialPartition(n)]
    for idx in range(1, n):
      before = list(raw_partitions[idx-1] - raw_partitions[idx])[0]
      left, right = list(raw_partitions[idx] - raw_partitions[idx-1])
      partitions.append(Split(partitions[idx-1], before, left, right))

    c = cls(partitions)
    assert repr(c) == s
    return c

  @staticmethod
  def min_dist_lb(n):
    return (n-2)*(n-1)/2

  def __str__(self):
    return ' -> '.join(str(p) for p in self)
  def __repr__(self):
    return ' -> '.join(repr(p) for p in self)

  # Returns the 0-based depth at which a and b first split.
  def split_depth(self, i, j):
    # TODO cache results
    return next(d for d, split in enumerate(self) if split.splits(i, j))

  def pushed_down(self, d, i, j):
    """Return a copy of this chain with partitions at d and d+1 modified so that i and j are split
    at depth d+1 instead of d."""
    ret = Chain(self[:])
    ret[d:d+2] = self.__swapped(self[d], self[d+1], i, j)
    return ret

  @staticmethod
  def __swapped(split1, split2, i, j):
    # split1 is where i and j are split.
    # We want to make a new (ret1, ret2) that have the same result as (split1, split2), but where
    # i and j are split in ret2 instead of ret1.
    if split2.before in [split1.left, split1.right]:
      # Then split2.before has exactly one of i or j. Pick the side of split2 that has neither and
      # split it off.
      uninvolved = split2.left if (i not in split2.left and j not in split2.left) else split2.right
      ret1 = Split.from_side(split1.parent, split1.before, uninvolved)
      # Now split i and j.
      # unsplit_side is the side of split1 that didn't get split by split2; it contains i or j (not
      # both) and will be used as one side of ret2.
      unsplit_side = split1.left if (split1.left != split2.before) else split1.right
      ret2 = Split.from_side(ret1, ret1.right, unsplit_side)
      return (ret1, ret2)
    else:
      # The parts getting split are unrelated; simply swap their order.
      ret1 = Split(split1.parent, split2.before, split2.left, split2.right)
      ret2 = Split(ret1, split1.before, split1.left, split1.right)
      return (ret1, ret2)

class ChainPath:
  """Implements an algorithm to find a path from one chain to another."""

  def __init__(self, chain1, chain2):
    self.chain1 = chain1
    self.chain2 = chain2

    # The algorithm finds a path bridging the chains by performing repeated operations to build two
    # paths from the original chains, until the paths converge.
    self.path1 = [chain1]
    self.path2 = [chain2]

  def path(self):
    """Returns the path found by find(), which must be called before this method."""
    return itertools.chain(self.path1, reversed(self.path2[:-1]))

  def print_results(self):
    """Prints the path found for human interpretation."""
    for c in self.path():
      # Flag the common point where both paths merged; useful for examining results.
      flag = ' *' if c == self.path1[-1] else ''
      print '%s%s' % (c, flag)

  def find(self, debug=False):
    """Actually runs the algorithm. Returns the resulting path as a list."""
    n = len(self.chain1)
    self.picked = set()

    for d in xrange(n-1, -1, -1):
      try:
        i, j = self.__next_i_j(d)
      except ValueError:
        # Not finding anything means we are done.
        break

      self.picked.add((i, j))
      self.__push_down(self.path1, d, i, j)
      self.__push_down(self.path2, d, i, j)

      if debug:
        print("Pushing (%d,%d) split down to depth %d from depths (%d, %d)"
              % (i,j,d, self.path1[-1].split_depth(i,j), self.path2[-1].split_depth(i,j)))

    # Check that the paths do converge (they will as long as the algorithm is correct) and return.
    assert self.path1[-1] == self.path2[-1]
    return self.path()

  def __next_i_j(self, d):
    n = len(self.chain1)

    # Enumerate all possible remaining pairs and the depths at which they are split in each chain.
    pairs = ((i, j, self.path1[-1].split_depth(i, j), self.path2[-1].split_depth(i, j))
             for i, j in itertools.combinations(range(1, n+1), 2)
             if (i, j) not in self.picked)
    # Eliminate pairs that are already split below the current depth in both chains.
    pairs = ((i, j, d1, d2) for i, j, d1, d2 in pairs if d1 < d or d2 < d)
    # Calculate d_{c1,c2} and pick the minimum.
    min_dist, i, j = min((2*n - d1 - d2, i, j) for i, j, d1, d2 in pairs)
    return i, j

  @staticmethod
  def __push_down(path, end_depth, i, j):
    chain = path[-1]
    start_depth = chain.split_depth(i, j)
    for depth in xrange(start_depth, end_depth):
      path.append(path[-1].pushed_down(depth, i, j))
    return path

def random_chain_paths():
  """Measures paths between randomized chains with a range of lengths."""
  for n in range(3, 20):
    for _ in range(5):
      print "n = %d" % n
      c1, c2 = Chain.random(n), Chain.random(n)
      print "Going from\n%s to\n%s" % (c1, c2)

      p = ChainPath(c1, c2)
      p.find()
      # p.print_results()

      print("Found path of length %d, we know we can do it in at most %d"
            % (len(list(p.path())), Chain.min_dist_lb(n)))
      print

def compare_path_lengths(lengths_file):
  diffs = [0] * 10

  with open(lengths_file, 'rb') as f:
    reader = csv.reader(f)
    for row in reader:
      chain1 = Chain.from_string(row[0])
      chain2 = Chain.from_string(row[1])
      optimal_length = int(float(row[2]))
      found_length = len(list(ChainPath(chain1, chain2).find())) - 1

      assert optimal_length <= found_length
      diffs[found_length - optimal_length] += 1

      print "%r to \n%r\n%d path found, optimal length %d" % (chain1, chain2, found_length, optimal_length)

  print
  for diff, count in enumerate(diffs):
    print "%d: %5d" % (diff, count)

def solve_path(from_chain, to_chain):
  chain1 = Chain.from_string(from_chain)
  chain2 = Chain.from_string(to_chain)
  cp = ChainPath(chain1, chain2)
  cp.find(debug=True)
  cp.print_results()

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("from_chain", help="a string representation of a chain; remember to use quotes",
                      nargs="?")
  parser.add_argument("to_chain", help="a string representation of a chain; remember to use quotes",
                      nargs="?")
  parser.add_argument("--random", help="generate and solve random problems", action="store_true")
  parser.add_argument("--from-file", help="read chains from file and compare with optimal lengths",
                      action="store_true")
  parser.add_argument("--lengths-file", help="location to read chains and lengths",
                      default="lengths.csv")
  args = parser.parse_args()

  if args.from_file:
    compare_path_lengths(args.lengths_file)
  elif args.random:
    random_chain_paths()
  else:
    if not args.from_chain or not args.to_chain:
      print "Please specify chains to go from and to:"
      print "%s '1.2.3.4 -> 1.2|3.4 -> 1|2|3.4 -> 1|2|3|4' '1.2.3.4 -> 1.3.4|2 -> 1.4|2|3 -> 1|2|3|4'"
      sys.exit(1)

    solve_path(args.from_chain, args.to_chain)

if __name__ == "__main__": main()
