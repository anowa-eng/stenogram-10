from datetime import datetime
from pathlib import Path
import re
import subprocess

from g2p_en import G2p

from src.alignments import Alignments
from tests.configure_logger import configure_logger


# ---------------------------------------------------------------------------- #
#                                     Setup                                    #
# ---------------------------------------------------------------------------- #

# ---------------------------------- Logging --------------------------------- #

g2p_logger = configure_logger('g2p')

g2p_logger.info('Loading g2p_en model...')
g2p = G2p()
g2p_logger.info('g2p_en model loaded.')

# ----------------------------------- Paths ---------------------------------- #

M2M_ALIGNER_CONTAINER_DIR = Path(__file__).parent.parent / 'aligner'
M2M_ALIGNER_DIR = M2M_ALIGNER_CONTAINER_DIR / 'm2m-aligner'
M2M_ALIGNER_EXECUTABLE = M2M_ALIGNER_DIR / 'm2m-aligner'
M2M_ALIGNER_MODEL = M2M_ALIGNER_CONTAINER_DIR / 'model/cmudict.txt.m-mAlign.2-2.delX.1-best.conYX.align.model'
M2M_ALIGNER_VAR_DIR = M2M_ALIGNER_CONTAINER_DIR / 'var'

# ---------------------------------------------------------------------------- #
#                                 Aligner class                                #
# ---------------------------------------------------------------------------- #

class Aligner:
    '''
    A class for aligning words using the m2m-aligner model.'''

    Nodes = list[str]
    Layer = list[Nodes]
    Word = list[Layer, Layer]
    Output = list[Word]

    @staticmethod
    def align(phrase: str) -> 'Aligner.Output':
        '''
        Aligns the given phrase using the m2m-aligner model.

        Args:
            phrase: The phrase to be aligned.
        
        Returns:
            Aligner.Output: A list of aligned word-phoneme pairs, separated by bars and colons.
        '''
        word_phoneme_pairs = Aligner._word_phoneme_pairs_g2p_en(phrase)
        m2m_out = Aligner._m2m_align(word_phoneme_pairs)
        out = [
            [Aligner._separate_word_phoneme_pair_by_bars_and_colons(string)
            for string in g2p_pair]
            for g2p_pair in m2m_out
        ]

        return out

    @staticmethod
    def _m2m_align(word_phoneme_pairs: list[tuple]):
        '''
        Uses m2m-aligner to align the given word-phoneme pairs.

        Args:
            word_phoneme_pairs: A list of (word, phonemes) tuples.
        
        Returns:
            List[List[str]]: A list of aligned word-phoneme pairs, separated by bars and colons.
        '''
        strftime = datetime.now().strftime('%Y%m%d_%H%M%S')
        input_file_path = M2M_ALIGNER_VAR_DIR / f'alignments_{strftime}_in'
        output_file_path = M2M_ALIGNER_VAR_DIR / f'alignments_{strftime}_out'
        with open(input_file_path, 'w') as f:
            contents = ''
            for word, phonemes in word_phoneme_pairs:
                contents += chr(32).join([*word])
                contents += '\t'
                contents += re.sub(r"\d\b", "", chr(32).join(phonemes))
                contents += '\n'
            f.write(contents)
        
        subprocess.run(
            f"'{M2M_ALIGNER_EXECUTABLE}' --delX --maxX 2 --maxY 2 --init '{M2M_ALIGNER_MODEL}' \
                --alignerIn '{M2M_ALIGNER_MODEL}' -o '{output_file_path}' -i '{input_file_path}'", cwd=M2M_ALIGNER_CONTAINER_DIR, 
            shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        with open(output_file_path, 'r') as f:
            m2m_out = f.read().rstrip()
            output_split_by_lines = m2m_out.split('\n')
            output_split_by_tabs = [line.split('\t') for line in output_split_by_lines]

        for i in M2M_ALIGNER_VAR_DIR.iterdir():
            if i.is_file():
                i.unlink()
        
        return output_split_by_tabs
    
    # ----------------------------- Helper functions ----------------------------- #
    @staticmethod
    def _word_phoneme_pairs_g2p_en(phrase: str):
        '''
        Generates ARPABET pronunciations for the given phrase using `g2p_en`, and separates them into a tuple consisting of the word and its phonemes.

        Args:
            phrase: The phrase to be aligned.
        
        Returns:
            List[tuple]: A list of (word, phonemes) tuples.
        '''
        phonemes: list = g2p(phrase)

        phonemes_by_word = Aligner._split_by_spaces(phonemes)
        words = phrase.split(' ')

        return list(zip(words, phonemes_by_word))

    @staticmethod
    def _split_by_spaces(g2p_output: list) -> 'Aligner.Layer':
        '''
        Takes in output from the g2p_en model and splits it by spaces, organizing the words into lists.

        Args:
            g2p_output: The output from the g2p_en model.

        Returns:
            Aligner.Layer: A list of lists, where each list contains the phonemes for a word.
        '''
        out = [[]]
        for phone in g2p_output:
            if phone == ' ':
                out.append([])
            else:
                out[-1].append(phone)
        return out
    
    @staticmethod
    def _separate_word_phoneme_pair_by_bars_and_colons(m2m_output: str) -> 'Aligner.Word':
        '''
        Separates the output from m2m-aligner by bars and colons.

        Args:
            m2m_output: The output from m2m-aligner.
        
        Returns:
            Aligner.Word: The output from m2m-aligner, split by bars and colons.
        '''
        out = m2m_output.split('|')
        out = [i.split(':') for i in out]
        return out[:-1]
    

# ---------------------------------------------------------------------------- #
#                             A little test script                             #
# ---------------------------------------------------------------------------- #

if __name__ == '__main__':
    print('Type ".exit" to stop.')

    string_ = ''
    while string_ != '.exit':
        string_ = input('>>> ')
        print(Aligner.align(string_))