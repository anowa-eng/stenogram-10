# not even a pytest

from src.aligner import Aligner
from src.alignments import Alignments

uinput = ""

print('oh hello there. enter a phrase to align, or ".exit" to quit.')
while uinput != ".exit":
    uinput = input('>>> ')
    if uinput == ".exit":
        break
    else:
        alignments = Alignments._from_aligner_output(Aligner.align(uinput))
        print(alignments)