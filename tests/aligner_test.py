# not even a pytest

from src.alignments.alignments import Alignments, bindings_logger

uinput = ""

print('oh hello there. enter a phrase to align, or ".exit" to quit.')
while True:
    uinput = input('>>> ')
    if uinput == ".exit":
        break
    else:
        bindings_logger.disabled = True
        alignments = Alignments.alignments_from_text(uinput)
        print(alignments)