import asyncio
from collections import deque
from dataclasses import dataclass, field
import re
from uuid import uuid4

from src.aligner5 import m2m_aligner
from src.aligner5.process import fmt_input_word, fmt_phonemes, output_line_is_word, postprocess
from src.aligner5.word import Word

def generate_filename(mode: str, func=uuid4) -> str:
    return str(m2m_aligner.VAR_DIR) + '/' + mode + '-' + str(func())

@dataclass
class WordGroupAligner:
    '''
    A class for aligning words using the m2m-aligner model.
    '''

    words: list[Word] = field(init=False, default_factory=list)
    input_file: str = field(init=False, default=generate_filename('in'))
    output_file: str = field(init=False, default=generate_filename('out'))

    def add_word(self, word: Word) -> None:
        self.words.append(word)
        word.subscribed_to = self

    # ------------------------------ Align the words ----------------------------- #

    def write_to_file(self) -> None:
        with open(self.input_file, 'w+') as f:
            if self.words:
                for word in self.words[:-1]:
                    line = fmt_input_word(word) + '\n'
                    if line not in f.readlines():
                        f.write(fmt_input_word(word) + '\n')

                f.write(fmt_input_word(self.words[-1]))
                # make sure that there aren't empty lines - empty lines are a waste of resources

    async def m2m_aligner_output(self) -> str:
        await m2m_aligner.m2m_aligner(
            init=m2m_aligner.MODEL,
            maxX=2,
            maxY=2,
            alignerIn=m2m_aligner.MODEL,
            o=self.output_file,
            i=self.input_file
        )

        return open(self.output_file, 'r')
        
    # ---------------------------------------------------------------------------- #

    async def align(self) -> None:
        self.write_to_file()
        output_file = await self.m2m_aligner_output()

        deques: list[deque[int]] = []

        for line in output_file.readlines():

            deques = [deque(range(len(self.words)))]

            for idx in deques[0]:
                word = self.words[idx]
                
                if output_line_is_word(word, line):
                    word.alignments = postprocess(word, line)
                
                next_deque = deques[-1].copy()
                next_deque.remove(idx)
                deques.append(next_deque)
            
                del deques[0]
        
        del deques

# ---------------------------------------------------------------------------- #

async def align_text(text: str) -> list[Word]:
    words = Word.list_from_text(text)
    print(words)

    aligner = WordGroupAligner()

    for word in words:
        if not word.is_expanded and not re.fullmatch(Word.punctuation_regex, word.long_form):
            aligner.add_word(word)

    await aligner.align()

    # for words that have no alignments
    for word in words:
        if not word.alignments:
            # there might be some logic here for numbers
            # but this is good enough.
            # progress > perfection        -anova9x
            phonemes = [*word.long_form] if re.fullmatch(Word.punctuation_regex, word.long_form) else fmt_phonemes(word.pronunciation).split()
            
            word.alignments = [[[*word.long_form]], [phonemes]]

    return words

# ---------------------------------------------------------------------------- #

async def test1():
    print(await align_text('destroying my mental well being with programming sure is fun!!'))



asyncio.run(test1())