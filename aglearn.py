#!/usr/bin/env python
"""
Simple baseline strategies for learning artifical language grammars.
"""

# Copyright (C) 2011-2012 Constantine Lignos
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
from collections import defaultdict

SYMBOLS = ('a', 'c', 'd', 'e', 'f', 'g')


class AGLearner:
    """A simple artificial language grammar learner."""

    def __init__(self):
        self.counts = defaultdict(int)
        self.cooccurs = defaultdict(lambda: defaultdict(int))

    def train(self, train_path):
        """Train based on the provided data."""
        with open(train_path, "Ur") as train_file:
            for line in train_file:
                line_symbols = line.split()
                
                for idx1, sym1 in enumerate(line_symbols):                    
                    # Count the symbol
                    self.counts[sym1] += 1

                    # Get the set of the other items and count co-occurences
                    other_symbols = set(line_symbols[:idx1] + line_symbols[idx1 + 1:])

                    # Count cooccurences
                    for sym2 in other_symbols:                
                        self.cooccurs[sym1][sym2] += 1
                                         

    def report(self):
        """Report the rules learned."""

        for sym1 in SYMBOLS:
            for sym2 in SYMBOLS:
                count1 = self.counts[sym1]

                if self.cooccurs[sym1][sym2] == count1:
                    print sym1, "requires", sym2
                elif self.cooccurs[sym1][sym2] == 0:
                    print sym1, "excludes", sym2


def main():
    """Call the learner and report."""
    try:
        in_path = sys.argv[1]
    except IndexError:
        print >> sys.stderr, "Usage: aglearn file"

    learner = AGLearner()
    learner.train(in_path)
    learner.report()
    

if __name__ == "__main__":
    main()
