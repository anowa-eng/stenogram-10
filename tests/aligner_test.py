# not even a pytest

from src.aligner import Aligner
from src.alignments.alignments import Alignments, bindings_logger

uinput = ""

print('oh hello there. enter a phrase to align, or ".exit" to quit.')
while True:
    uinput = input('>>> ')
    if uinput == ".exit":
        break
    else:
        bindings_logger.disabled = True
        m2m_aligner_output = Aligner._m2m_align(Aligner._word_phoneme_pairs_g2p_en(uinput))
        alignments = Alignments._from_aligner_output(Aligner.align(uinput))
        print(m2m_aligner_output)
        print(alignments)