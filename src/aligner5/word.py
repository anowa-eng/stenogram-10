from dataclasses import dataclass, field
import re
from typing import Callable

from Aquila_Resolve.text import numbers
from Aquila_Resolve import G2p

aquila_resolve_g2p = G2p()

# ---------------------------------------------------------------------------- #
#                                  Word class                                  #
# ---------------------------------------------------------------------------- #

def _combine_regexes(*regexes: list[re.Pattern]) -> re.Pattern:
    rgx = ['(' + rgx_.pattern + ')' for rgx_ in regexes]

    rgx = '|'.join(rgx)

    return re.compile(rgx)

@dataclass
class Word:
    short_form: str
    long_form: str = field(init=False)
    pronunciation: str = field(init=False)

    g2p_function: Callable[[str], str] = field(repr=False, default=aquila_resolve_g2p.convert)
    normalize_numbers_function: Callable[[str], str] = field(repr=False, default=numbers.normalize_numbers)

    alignments: str = field(init=False, default=None)

    punctuation_regex = re.compile(r"[^$€£₩,\.'\w\s]|(?<![0-9])[\.,]+(?![0-9])|\s(?![fckdm]\b|km\b|ft\b)|(?<=[^0-9])\s")
    splitting_regex = _combine_regexes(
        numbers._decimal_number_re,
        numbers._comma_number_re,
        numbers._currency_re,
        numbers._ordinal_re,
        numbers._measurement_re,
        numbers._roman_re,
        numbers._multiply_re,
        numbers._number_re,
        punctuation_regex
    )

    def __post_init__(self):
        self.long_form = self.normalize_numbers_function(self.short_form)
        self.pronunciation = self.g2p_function(self.long_form)

        self.subscribed_to: 'Aligner' = None

    @property
    def is_expanded(self) -> bool:
        return self.short_form != self.long_form
    
    # ---------------------------------------------------------------------------- #

    @staticmethod
    def separate_unexpanded_symbols(text_line: str):
        matches = list(re.finditer(Word.splitting_regex, text_line))

        # https://stackoverflow.com/questions/47853171/how-to-split-a-string-with-regexp-without-keeping-capture-groups
        delimiter = '<<split>>'
        non_matches = re.sub(Word.splitting_regex, delimiter, text_line).split(delimiter)

        original_len = len(non_matches)
        for i, match in enumerate(matches[::-1]):
            print(match.group())
            non_matches.insert((original_len - 1) - i, match.group())

        result = [text for text in non_matches if text != ''] if len(non_matches) > 0 else non_matches

        return result

    @staticmethod
    def list_from_text(text_line: str) -> list['Word']:
        if text_line == '':
            return []
        
        return [Word(word) for word in Word.separate_unexpanded_symbols(text_line)]
