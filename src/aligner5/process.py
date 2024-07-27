import re

from Aquila_Resolve.text import numbers

from src.aligner5.word import Word

# ---------------------------------------------------------------------------- #
#                               Type definitions                               #
# ---------------------------------------------------------------------------- #

class Processor:
    Nodes = list[str]
    Layer = list[Nodes]
    AlignerWord = list[Layer, Layer]
    Output = list[AlignerWord]

# ---------------------------------------------------------------------------- #
#                            Preprocessing utilities                           #
# ---------------------------------------------------------------------------- #


braces_re = re.compile(r"\{[^}]*\}")

def fmt_graphemes(graphemes: str) -> str:
    graphemes = re.sub(r'[^\w]+', '', graphemes)
    return chr(32).join(graphemes.lower())
    
def fmt_remove_stress_marks(phonemes: str) -> str:
    return re.sub(r'\d\b', '', phonemes)

def fmt_phonemes(phonemes: str) -> str:
    individual_pronunciations = re.finditer(braces_re, phonemes)

    phonemes = []
    for individual_pronunciation in individual_pronunciations:
        match = individual_pronunciation.group(0)

        start = 1
        stop = -1

        arpabet = match[start:stop]

        phonemes.append(fmt_remove_stress_marks(arpabet))

    phonemes = chr(32).join(phonemes)

    return phonemes

def fmt_input_word(word: Word) -> str:
    return fmt_graphemes(word.long_form) + '\t' + fmt_phonemes(word.pronunciation)


def remove_bars_colons(text: str) -> str:
    return re.sub(r'[\|:]', ' ', text).rstrip()

def output_line_is_word(word: Word, output_line: str) -> bool:
    # assuming that the words are formatted
    graphemes, phonemes = output_line.split('\t')

    graphemes_match = fmt_graphemes(word.long_form) == remove_bars_colons(graphemes)
    phonemes_match = fmt_phonemes(word.pronunciation) == remove_bars_colons(phonemes)

    return graphemes_match and phonemes_match

# ---------------------------------------------------------------------------- #
#                           Post-processing utilities                          #
# ---------------------------------------------------------------------------- #

split_grapheme_line_re = re.compile(r'[\|:]|[^\|:]')
punctuation_letter_cluster_re = re.compile(r'[^\w]*\w')

def split_word_into_punctuation_letter_clusters(word_long_form: str) -> list[str]:
    return re.findall(punctuation_letter_cluster_re, word_long_form)

def re_add_disallowed_m2m_aligner_characters(word: Word, grapheme_line: str) -> str:
    fixed_output = re.findall(split_grapheme_line_re, grapheme_line)

    position_of_tab = fixed_output.index('\t')
    fixed_output[:position_of_tab:2] = split_word_into_punctuation_letter_clusters(word.long_form)

    return ''.join(fixed_output)

def split_aligner_output(aligned_data: str) -> Processor.Output:
    aligned_data = aligned_data.split('\n')

    aligned_data = [i.split('\t') for i in aligned_data]

    data_split = [
        [[k.split(':') for k in j.split('|')[:-1]] for j in i] for i in aligned_data
    ]

    return data_split


def postprocess(word: Word, aligner_line: str) -> Processor.Output:
    aligner_line = re_add_disallowed_m2m_aligner_characters(word, aligner_line[:-1])
    aligner_output = split_aligner_output(aligner_line)[0]

    return aligner_output

