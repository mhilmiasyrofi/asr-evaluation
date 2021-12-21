# Copyright 2017-2018 Ben Lambert

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""
Primary code for computing word error rate and other metrics from ASR output.
"""
from __future__ import division

from collections import defaultdict
from edit_distance import SequenceMatcher


class ASREvaluation(object):

    # Tables for keeping track of which words get confused with one another
    insertion_table = defaultdict(int)
    deletion_table = defaultdict(int)
    substitution_table = defaultdict(int)

    # These are the editdistance opcodes that are condsidered 'errors'
    error_codes = ['replace', 'delete', 'insert']

    min_count = 0

    def __init__(self):
        pass

    def detect_word_error(self, ref_line, hyp_line, case_insensitive=False, remove_empty_refs=False):
        """Given a pair of strings corresponding to a reference and hypothesis,
        compute the edit distance, print if desired, and keep track of results
        in global variables.

        Return true if the pair was counted, false if the pair was not counted due
        to an empty reference string."""

        self.insertion_table = defaultdict(int)
        self.deletion_table = defaultdict(int)
        self.substitution_table = defaultdict(int)

        # Split into tokens by whitespace
        ref = ref_line.split()
        hyp = hyp_line.split()

        if case_insensitive:
            ref = list(map(str.lower, ref))
            hyp = list(map(str.lower, hyp))
        if remove_empty_refs and len(ref) == 0:
            return False

        # Create an object to get the edit distance, and then retrieve the
        # relevant counts that we need.
        sm = SequenceMatcher(a=ref, b=hyp)
        self.track_confusions(sm, ref, hyp)
        return self.get_confusions()

    def track_confusions(self, sm, seq1, seq2):
        """Keep track of the errors in a global variable, given a sequence matcher."""
        
        opcodes = sm.get_opcodes()
        for tag, i1, i2, j1, j2 in opcodes:
            if tag == 'insert':
                for i in range(j1, j2):
                    word = seq2[i]
                    self.insertion_table[word] += 1
            elif tag == 'delete':
                for i in range(i1, i2):
                    word = seq1[i]
                    self.deletion_table[word] += 1
            elif tag == 'replace':
                for w1 in seq1[i1:i2]:
                    for w2 in seq2[j1:j2]:
                        key = (w1, w2)
                        self.substitution_table[key] += 1

    def get_confusions(self):
        """Get the confused words that we found... grouped by insertions, deletions
        and substitutions."""
        
        res = {}
        res["insertion"] = []
        res["deletion"] = []
        res["substitution"] = []
        if len(self.insertion_table) > 0:
            for item in sorted(list(self.insertion_table.items()), key=lambda x: x[1], reverse=True):
                if item[1] >= self.min_count:
                    # print('{0:20s} {1:10d}'.format(*item))
                    res["insertion"].append({"word": item[0], "count": item[1]})
        if len(self.deletion_table) > 0:
            for item in sorted(list(self.deletion_table.items()), key=lambda x: x[1], reverse=True):
                if item[1] >= self.min_count:
                    # print('{0:20s} {1:10d}'.format(*item))
                    res["deletion"].append({"word": item[0], "count": item[1]})

        if len(self.substitution_table) > 0:
            # print('SUBSTITUTIONS:')
            for [w1, w2], count in sorted(list(self.substitution_table.items()), key=lambda x: x[1], reverse=True):
                if count >= self.min_count:
                    # print('{0:20s} -> {1:20s}   {2:10d}'.format(w1, w2, count))
                    res["substitution"].append({"word_reference": w1, "word_substitution": w2, "count": count})
        
        return res
