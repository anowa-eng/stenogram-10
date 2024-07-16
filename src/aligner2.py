# ---------------------------------------------------------------------------- #
#                           * * * experimental * * *                           #
# ---------------------------------------------------------------------------- #

import re

from collections import defaultdict
from g2p_en.expand import abbreviations, time_norm, number_norm

class Aligner2:
    _split_re = re.compile(r"[^\w\s']+|\w+")

    def split(text: str) -> list:
        return Aligner2._split_re.findall(text)

    def _indices(text: str) -> list:
        result = defaultdict(list)

        words = text.split()
        for i, word in enumerate(words):
            result[word].append(i)

        return dict(result)

    def _unexpanded_words(text: str, expanded_text: str):
        words = text.split()
        indices = Aligner2._indices(text)

        for word in expanded_text.split():
            if word in words:
                idx = indices[word][0]
                yield (idx, word)
                indices[word].pop(0)
            

    def expand(text: str) -> list:
        result = text

        result = abbreviations.expand_abbreviations(result)
        result = time_norm.expand_time(result)
        result = number_norm.expand_numbers(result)

        result = result.replace(",", "")
        result = result.replace(":", " ")

        unexpanded_words = Aligner2._unexpanded_words(text, result)

        return {
            "result": result,
            "unexpanded_words": list(zip(*unexpanded_words))
        }

# ---------------------------------------------------------------------------- #

print(Aligner2.expand('jargon divert antler 292929 £1050515 time note pliers $3141 51% centipede blind eye gnomes'))