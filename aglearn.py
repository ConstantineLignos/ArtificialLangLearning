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

from ngram import NgramModel

SYMBOLS = ('a', 'c', 'd', 'e', 'f', 'g')
START_SYM = "^"
END_SYM = "$"

class AGLearner:
    """A simple artificial language grammar learner."""

    def __init__(self):
        # Input counts
        # Number of times each symbol is seen
        self.counts = defaultdict(int)
        # Number of times symbols co-occur
        self.cooccurs = defaultdict(lambda: defaultdict(int))
        # Whether a symbol is observed before or after another symbol
        self.before = {sym: set() for sym in SYMBOLS}
        self.after = {sym: set() for sym in SYMBOLS}

        # Learning structures
        self.requires = defaultdict(set)
        self.excludes = defaultdict(set)
        self.noprecede = defaultdict(set)
        self.nofollow = defaultdict(set)
        self.mustprecede = {sym: set(SYMBOLS) for sym in SYMBOLS}
        self.mustfollow = {sym: set(SYMBOLS) for sym in SYMBOLS}
        self.ngram = None

    def train(self, train_path):
        """Train based on co-occurences in the provided data."""
        term_symbols = []

        # Process input
        with open(train_path, "Ur") as train_file:
            for line in train_file:
                line_symbols = line.split()

                # Learn co-occurences and precedes/follows
                for idx, sym1 in enumerate(line_symbols):
                    # Count the symbol
                    self.counts[sym1] += 1

                    # Get the sets of the other items
                    preceding_symbols = set(line_symbols[:idx])
                    following_symbols = set(line_symbols[idx + 1:])
                    other_symbols = preceding_symbols | following_symbols

                    # Count cooccurences
                    for sym2 in other_symbols:
                        self.cooccurs[sym1][sym2] += 1

                    # Mark before/after
                    for sym2 in preceding_symbols:
                        self.before[sym1].add(sym2)
                    for sym2 in following_symbols:
                        self.after[sym1].add(sym2)

                    # Remove if one of the always relationships does
                    # not hold up
                    for sym2 in SYMBOLS:
                        if sym2 not in preceding_symbols:
                            try:
                                self.mustprecede[sym1].remove(sym2)
                            except KeyError:
                                pass
                        if sym2 not in following_symbols:
                            try:
                                self.mustfollow[sym1].remove(sym2)
                            except KeyError:
                                pass

                # Add beginning and end terminators for n-grams
                term_symbols.extend([START_SYM] + line_symbols + [END_SYM])

        # Learn
        # Requires/excludes and precedes/follows
        for sym1 in SYMBOLS:
            for sym2 in SYMBOLS:
                # Co-occurence counts imply requires/excludes
                count1 = self.counts[sym1]
                if self.cooccurs[sym1][sym2] == count1:
                    self.requires[sym1].add(sym2)
                elif self.cooccurs[sym1][sym2] == 0:
                    self.excludes[sym1].add(sym2)

                # Figure out what cannot precede/follow
                if sym2 not in self.before[sym1]:
                    self.noprecede[sym1].add(sym2)
                if sym2 not in self.after[sym1]:
                    self.nofollow[sym1].add(sym2)

        # N-gram model
        self.ngram = NgramModel(2, term_symbols)

    def report(self):
        """Report the rules learned."""
        print "Co-occurence rules:"
        for sym in SYMBOLS:
            print sym, "requires", ', '.join(sorted(self.requires[sym]))
            print sym, "excludes", ','.join(sorted(self.excludes[sym]))

        print
        print "Linear precedence rules:"
        for sym in SYMBOLS:
            print sym, "cannot be preceded by", ', '.join(sorted(self.noprecede[sym]))
            print sym, "cannot be followed by", ', '.join(sorted(self.nofollow[sym]))

        print
        print "N-grams:"
        for event, context, prob in self.ngram.allngrams():
            print "{0} -> {1}: {2}".format(' '.join(context), event, prob)

    def test(self, test_path, out_path):
        """Test on a file"""
        test_file = open(test_path, "Ur")
        out_file = open(out_path, "w")

        header = ["Sentence", "Gold response", "Co-occur response", "Co-occur reason",
                  "Linear response", "Linear reason", "N-gram prob."]
        print >> out_file, "\t".join(header)

        for line in test_file:
            sent, gold = line.strip().split(',')
            gold = (gold.strip() == "True")
            line_symbols = sent.split()
            line_symbols_term = [START_SYM] + line_symbols + [END_SYM]

            # Decode violations
            cooccur_ok = True
            cooccur_reasons = set()
            linear_ok = True
            linear_reasons = set()

            for idx, sym1 in enumerate(line_symbols):
                # Get the sets of the other items
                preceding_symbols = set(line_symbols[:idx])
                following_symbols = set(line_symbols[idx + 1:])
                other_symbols = preceding_symbols | following_symbols

                # Check requirements and exclusions for each pair
                # Excluded symbols that are present
                for sym2 in self.excludes[sym1] & other_symbols:
                    cooccur_ok = False
                    cooccur_reasons.add("{0} excludes {1}".format(sym1, sym2))
                # Required symbols that are missing
                for sym2 in self.requires[sym1] & (set(SYMBOLS) - other_symbols):
                    cooccur_ok = False
                    cooccur_reasons.add("{0} requires {1}".format(sym1, sym2))

                # Check that preceding/following symbols are okay
                for prec_sym in preceding_symbols:
                    if prec_sym in self.noprecede[sym1]:
                        linear_ok = False
                        linear_reasons.add("{1} cannot precede {0}".format(sym1, prec_sym))
                for fol_sym in following_symbols:
                    if fol_sym in self.nofollow[sym1]:
                        linear_ok = False
                        linear_reasons.add("{1} cannot follow {0}".format(sym1, fol_sym))

                # Check for missing preceding/following symbols
                for prec_sym in self.mustprecede[sym1] - preceding_symbols:
                    linear_ok = False
                    linear_reasons.add("{1} must precede {0}".format(sym1, prec_sym))
                for fol_sym in self.mustfollow[sym1] - following_symbols:
                    linear_ok = False
                    linear_reasons.add("{1} must follow {0}".format(sym1, fol_sym))

            # N-gram statistics
            prob = self.ngram.seqprob(line_symbols_term)

            # Output
            print >> out_file, "\t".join([" ".join(line_symbols), str(gold),
                                          str(cooccur_ok), ", ".join(cooccur_reasons),
                                          str(linear_ok), ", ".join(linear_reasons),
                                          str(prob)])

        # Clean up
        test_file.close()
        out_file.close()


def main():
    """Call the learner and report."""
    try:
        train_path = sys.argv[1]
        test_path = sys.argv[2]
        out_path = sys.argv[3]
    except IndexError:
        print >> sys.stderr, "Usage: aglearn train test output"
        sys.exit(64)

    learner = AGLearner()
    learner.train(train_path)
    learner.test(test_path, out_path)
    print
    learner.report()


if __name__ == "__main__":
    main()
