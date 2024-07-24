import os
from pathlib import Path
import re
import subprocess
from typing import List, Mapping, Tuple
from uuid import uuid4

from src.aligner4.pronunciation import Pronunciation, SingleMatchPronunciation


M2M_ALIGNER_CONTAINER_DIR = Path(__file__).parent.parent.parent / 'aligner'
M2M_ALIGNER_DIR = M2M_ALIGNER_CONTAINER_DIR / 'm2m-aligner'
M2M_ALIGNER_EXECUTABLE = M2M_ALIGNER_DIR / 'm2m-aligner'
M2M_ALIGNER_MODEL = M2M_ALIGNER_CONTAINER_DIR / 'model/cmudict.txt.m-mAlign.2-2.delX.1-best.conYX.align.model'
M2M_ALIGNER_VAR_DIR = M2M_ALIGNER_CONTAINER_DIR / 'var'


class Aligner4Formatter:
    @staticmethod
    def remove_stress_marks(text: str) -> str:
        return re.sub(r'\d\b', '', text)
    
    @staticmethod
    def format_graphemes(text: str) -> str:
        return chr(32).join(text)
    
    @staticmethod
    def format_phonemes(arpabet_output: str) -> str:
        return Aligner4Formatter.remove_stress_marks(
            arpabet_output[1:-1]
        )
    
    @staticmethod
    def format(graphemes: str, phonemes: str) -> str:
        return Aligner4Formatter.format_graphemes(graphemes) + '\t' + Aligner4Formatter.format_phonemes(phonemes)

# ---------------------------------------------------------------------------- #

class _M2MAlignerService:
    '''
    A class with utility functions to run m2m-aligner and extract its output.
    '''
    def _align_file_content(formatted_content: str, delete=True) -> Mapping[str, str]:
        """
        Runs the M2M aligner with the provided formatted content, and returns the aligned and unaligned data.
        
        Parameters:
            formatted_content (str): The content to be formatted and aligned.
            delete (bool, optional): Flag to delete the input, output, and unaligned data files. Defaults to True.
        
        Returns:
            dict: A dictionary containing the aligned data and unaligned data.
        """
        uuid_ = uuid4()

        input_file_path = M2M_ALIGNER_VAR_DIR / f'in-{uuid_}.txt'
        output_file_path = M2M_ALIGNER_VAR_DIR / f'out-{uuid_}.txt'
        unaligned_data_path = M2M_ALIGNER_VAR_DIR / f'out-{uuid_}.txt.err'

        with open(input_file_path, 'x') as file:
            file.write(formatted_content)

        subprocess.run(
            f"'{M2M_ALIGNER_EXECUTABLE}' --delX --maxX 2 --maxY 2 --init '{M2M_ALIGNER_MODEL}' --alignerIn '{M2M_ALIGNER_MODEL}' -o '{output_file_path}' -i '{input_file_path}'", cwd=M2M_ALIGNER_CONTAINER_DIR, 
            shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        # - - - - - - - - - - - - - - - - - - - - - - - - #

        aligned_data = ''

        with open(output_file_path, 'r') as file:
            aligned_data = file.read()[:-1]

        with open(unaligned_data_path, 'r') as file:
            unaligned_data = file.read()
        
        if delete:
            os.remove(input_file_path)
            os.remove(output_file_path)
            os.remove(unaligned_data_path)

        return {
            "aligned_data": _M2MAlignerService._split_aligner_output(aligned_data),
            "unaligned_data": unaligned_data
        }
    

    @staticmethod
    def _split_aligner_output(aligned_data: str):
        aligned_data = aligned_data.split('\n')

        aligned_data = [i.split('\t') for i in aligned_data]

        data_split = [
            [[k.split(':') for k in j.split('|')[:-1]] for j in i] for i in aligned_data
        ]

        return data_split
    

    @staticmethod
    def align_graphemes_to_phonemes(g2p_pairs: List[Tuple[str, str]], delete=True):
        formatted_content = '\n'.join([
            Aligner4Formatter.format(graphemes, phonemes)
            for graphemes, phonemes in g2p_pairs
        ])

        return _M2MAlignerService._align_file_content(formatted_content)




# ---------------------------------------------------------------------------- #
#                                    testing                                   #
# ---------------------------------------------------------------------------- #

test_p = Pronunciation('twenty').pronunciation.__next__()
test_a = _M2MAlignerService().align_graphemes_to_phonemes([(test_p.expanded_form, test_p.pronunciation[0])], delete=False)

print(test_a)