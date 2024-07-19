# ---------------------------------------------------------------------------- #
#                           * * * experimental * * *                           #
# ---------------------------------------------------------------------------- #
import os
from pathlib import Path
from pprint import pprint
import re
import subprocess
from uuid import uuid4

from collections import defaultdict
from typing import List, Mapping, Tuple, Union

from Aquila_Resolve.text.numbers import normalize_numbers
from Aquila_Resolve import G2p


class Pronunciation:
    # Types
    ExpansionResult = List[Tuple[str, str]]
    G2pInferenceTuple = Tuple[str, str, str]
    G2pInferenceTuples = List[G2pInferenceTuple]

    _g2p = G2p()

    _split_re = re.compile(
        r"[!\"#%&()*+,\-./;<=>?@[\\\]^_`{|}~]+|[^!\"#%&()*+,\-./:;<=>?@[\\\]^_`{|}~ ]+"
    )
    _g2p_re = re.compile(r"\{[^\}]+\}|[^\{\} ]+")

    @staticmethod
    def _split(text: str) -> list:
        '''
        Splits the text into words using the _split_re regex, with punctuation
        '''
        return Pronunciation._split_re.findall(text)

    @staticmethod
    def expand(text: str) -> dict:
        mapping = Pronunciation._split(text)

        mapping = [
            (word, normalize_numbers(word) \
                .replace(':', ' ') \
                .replace(',', '')) \
            for word in mapping
        ]

        expansion_indices = defaultdict(list)

        values = list(zip(*mapping))[1]

        value_index = 0
        for i, expansion in enumerate(values):
            for j in expansion.split():
                expansion_indices[i].append(value_index)
                value_index += 1

        return {
            "result": chr(32).join(values),
            "word_mapping": mapping,
            "idx_mapping": dict(expansion_indices)
        }

    @staticmethod
    def pronunciation(
            words: str,
            return_expansions=False) -> Union[str, G2pInferenceTuples]:
        expanded = Pronunciation.expand(words)

        inference = Pronunciation._g2p.convert(words)

        if return_expansions:
            all_word_phonemes = Pronunciation._g2p_re.findall(inference)

            idx_mapping = expanded["idx_mapping"]
            respective_word_phones = []

            print(all_word_phonemes)

            try:
                for _, expansion_indices in idx_mapping.items():
                    respective_word_phones.append(
                        tuple(all_word_phonemes[i] for i in expansion_indices))
            except IndexError:
                return []

            individual_outputs = [
                *zip(*expanded['word_mapping']), respective_word_phones
            ]

            print(respective_word_phones)

            return list(zip(*individual_outputs))
        else:
            return inference or []


# ---------------------------------------------------------------------------- #

ALIGNER_DIR = Path(__file__).parent.parent / 'aligner'

M2M_ALIGNER_CONTAINER_DIR = Path(__file__).parent.parent / 'aligner'
M2M_ALIGNER_DIR = M2M_ALIGNER_CONTAINER_DIR / 'm2m-aligner'
M2M_ALIGNER_EXECUTABLE = M2M_ALIGNER_DIR / 'm2m-aligner'
M2M_ALIGNER_MODEL = M2M_ALIGNER_CONTAINER_DIR / 'model/cmudict.txt.m-mAlign.2-2.delX.1-best.conYX.align.model'
M2M_ALIGNER_VAR_DIR = M2M_ALIGNER_CONTAINER_DIR / 'var'


class Aligner2:
    '''
    Recognizes the correspondence between grapheme and phoneme.
    '''

    Nodes = list[str]
    Layer = list[Nodes]
    Word = list[Layer, Layer]
    Output = list[Word]

    Pairs = List[Tuple[str, str]]

    @staticmethod
    def _pairs_single_inference_tuple(
            inference: Pronunciation.G2pInferenceTuple) -> Pairs:
        _, words, phones = inference
        words = words.split()
        pairs = list(zip(words, phones))
        return pairs

    @staticmethod
    def _pairs(
        inference_tuples: Pronunciation.G2pInferenceTuples
    ) -> List[Tuple[str, str]]:
        pairs = []
        for inference in inference_tuples:
            pairs.extend(Aligner2._pairs_single_inference_tuple(inference))

        return pairs

    # ---------------------------------------------------------------------------- #

    @staticmethod
    def _news_format__single_pair(pair: Tuple[str, str]) -> str:
        print(f'{pair=}')
        graphemes, phonemes = pair

        fmt_graphemes = ' '.join(graphemes.lower())

        fmt_phonemes = phonemes.removeprefix('{').removesuffix('}')
        fmt_phonemes = re.sub(r'\d\b', '', fmt_phonemes)

        return fmt_graphemes + '\t' + fmt_phonemes

    @staticmethod
    def _news_format(pronunciation: Pronunciation.G2pInferenceTuples) -> str:
        pairs = Aligner2._pairs(pronunciation)
        return '\n'.join(
            Aligner2._news_format__single_pair(pair) for pair in pairs) + '\n'

    # ------------------ Run m2m-aligner (many-to-many aligner) ------------------ #

    @staticmethod
    def _run_m2m_aligner(formatted_content: str, delete=True) -> Mapping[str, str]:
        uuid_ = uuid4()

        input_file_path = M2M_ALIGNER_VAR_DIR / f'in-{uuid_}.txt'
        output_file_path = M2M_ALIGNER_VAR_DIR / f'out-{uuid_}.txt'
        unaligned_data_path = M2M_ALIGNER_VAR_DIR / f'out-{uuid_}.txt.err'

        with open(input_file_path, 'w') as file:
            file.write(formatted_content)

        subprocess.run(
            f"'{M2M_ALIGNER_EXECUTABLE}' --delX --maxX 2 --maxY 2 --alignerIn '{M2M_ALIGNER_MODEL}' -o '{output_file_path}' -i '{input_file_path}'", cwd=M2M_ALIGNER_CONTAINER_DIR, 
            shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        # - - - - - - - - - - - - - - - - - - - - - - - - #

        aligned_data = ''

        with open(output_file_path, 'r') as file:
            aligned_data = file.read()

        with open(output_file_path, 'r') as file:
            unaligned_data = file.read()
        
        if delete:
            os.remove(input_file_path)
            os.remove(output_file_path)
            os.remove(unaligned_data_path)

        return {
            "aligned_data": aligned_data,
            "unaligned_data": unaligned_data
        }

    @staticmethod
    def _split_aligner_output(aligned_data: str) -> Output:
        aligned_data = aligned_data.split('\n')
        print(aligned_data)

        aligned_data = [i.split('\t') for i in aligned_data]
        print(aligned_data)

        data_split = [
            [[k.split(':') for k in j.split('|')[:-1]] for j in i] for i in aligned_data
        ]

        return data_split

# ---------------------------------------------------------------------------- #

print(
    "hello there! type whatever you want and it will generate a breakdown for you of every word's expansions/phonemes. or type '.exit' to stop."
)

uinput = ''
while True:
    uinput = input('>>> ')
    if uinput == '.exit':
        break
    else:
        result = Pronunciation.pronunciation(uinput, True)
        content = Aligner2._news_format(result)
        output = Aligner2._run_m2m_aligner(content)
        print(Aligner2._split_aligner_output(output['aligned_data']))
