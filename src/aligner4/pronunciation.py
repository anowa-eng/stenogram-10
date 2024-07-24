from dataclasses import dataclass
from itertools import chain
import re
from typing import Iterator, List, Tuple

from Aquila_Resolve import G2p
from Aquila_Resolve.text import numbers

def regex(*regexes: List[re.Pattern]) -> re.Pattern:
    rgx = ['(' + rgx_.pattern + ')' for rgx_ in regexes]

    rgx = '|'.join(rgx)

    return re.compile(rgx)


rgx = regex(
    numbers._decimal_number_re,
    numbers._comma_number_re,
    numbers._currency_re,
    numbers._ordinal_re,
    numbers._measurement_re,
    numbers._roman_re,
    numbers._multiply_re,
    numbers._number_re,

    re.compile(r"[^\w']+")
)

# ---------------------------------------------------------------------------- #
_g2p_output_separation_re = re.compile(r"\{[^\}]*\}|[^\{\}]+")
_expanded_form_separation_re = re.compile(r"[\w'-]+|[^\w'-]+")

def separate_phonemes_from_punctuation(arpabet_output: str) -> Iterator[re.Match[str]]:
    '''
    Separates groups of phonemes, wrapped in braces, from whitespaces, punctuation symbols, etc.

    Returns: Iterator[re.Match[str]]
    '''
    return re.findall(_g2p_output_separation_re, arpabet_output)

def separate_expanded_form_from_punctuation(words: str) -> Iterator[re.Match[str]]:
    '''
    Separates words from whitespaces, punctuation symbols, etc.
    '''
    return re.finditer(_expanded_form_separation_re, words)

# ---------------------------------------------------------------------------- #

def _invert_match_spans(string: str, symbols_iter: Iterator) -> List[Tuple[int, int]]:
    symbols = list(symbols_iter)
    symbols = sorted(symbols, key=lambda x: x.span())

    result = []

    if len(symbols) == 0:
        return [(0, len(string))]
    else:
        if symbols[0].span()[0] != 0:
            result.append((0, symbols[0].span()[0]))

        for i in range(len(symbols) - 1):
            current_symbol = symbols[i]
            next_symbol = symbols[i + 1]

            start = current_symbol.span()[1]
            stop = next_symbol.span()[0]

            if start != stop:
                result.append((current_symbol.span()[1], next_symbol.span()[0]))

        if symbols[-1].span()[1] != len(string):
            result.append((symbols[-1].span()[1], len(string)))

    print(f'result: {result}')

    return result

def _convert_span_to_match(string: str, span: Tuple[int, int]) -> List[Tuple[int, int]]:
    start, stop  = span
    match_str = string[start:stop]

    regex = re.compile(
        (r'(?<=' + re.escape(string[:start]) + r')' if start > 0 else r'') +
        r'(' + re.escape(match_str) + r')' +
        (r'(?=' + re.escape(string[stop:]) + r')' if stop < len(string) else r'')
    )

    return re.search(regex, string)

def _convert_spans_to_matches(string: str, spans: List[Tuple[int, int]]) -> Iterator[re.Match]:
    return (_convert_span_to_match(string, span) for span in spans)

def _separate_words_from_symbols(string: str):
    symbols_to_be_expanded = [*re.finditer(rgx, string)]

    inverted_spans = _invert_match_spans(string, symbols_to_be_expanded)
    matches_to_be_left_alone = [*_convert_spans_to_matches(string, inverted_spans)]

    print(f'symbols_to_be_expanded: {symbols_to_be_expanded}')
    print(f'matches_to_be_left_alone: {matches_to_be_left_alone}')

    return sorted(
        chain(symbols_to_be_expanded, matches_to_be_left_alone),
        key=lambda x: x.span()
    )

# ---------------------------------------------------------------------------- #

_g2p = G2p()


@dataclass
class SingleMatchPronunciation:
    match: re.Match

    def symbol_is_expanded(self) -> bool:
        return re.fullmatch(rgx, self.match.group()) != []

    @property
    def expanded_form(self) -> str:
        if self.symbol_is_expanded():
            return numbers.normalize_numbers(self.match.group())
        else:
            return self.match.group()
    
    @property
    def expanded_form_re_matches(self) -> List[str]:
        return _separate_words_from_symbols(self.expanded_form)
    
    @property
    def expanded_form_split(self) -> str:
        return [m.group() for m in self.expanded_form_re_matches]
    
    @property
    def pronunciation(self) -> str:
        return separate_phonemes_from_punctuation(_g2p.convert(self.expanded_form))
    
    @staticmethod
    def from_list_of_matches(lst: List[re.Match]) -> Iterator["SingleMatchPronunciation"]:
        return (SingleMatchPronunciation(match) for match in lst)
    

class Pronunciation:
    def __init__(self, string: str):
        self.string = string
        
        self.all_matches_with_separated_words_from_punctuation = _separate_words_from_symbols(self.string)
        self.pronunciation = SingleMatchPronunciation.from_list_of_matches(self.all_matches_with_separated_words_from_punctuation)
    
