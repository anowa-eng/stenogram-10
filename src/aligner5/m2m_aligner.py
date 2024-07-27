from pathlib import Path
import subprocess

from tests.configure_logger import configure_logger


CONTAINER_DIR = Path(__file__).parent.parent.parent / 'aligner'
ALIGNER_DIR = CONTAINER_DIR / 'm2m-aligner'
EXECUTABLE = ALIGNER_DIR / 'm2m-aligner'
MODEL = CONTAINER_DIR / 'model/cmudict.txt.m-mAlign.2-2.delX.1-best.conYX.align.model'
VAR_DIR = CONTAINER_DIR / 'var'

logger = configure_logger('m2m-aligner')

async def m2m_aligner(**kwargs) -> None:
    """
    Runs the M2M aligner with the provided arguments.
    
    Parameters:
        kwargs (dict): A dictionary of arguments to be passed to the M2M aligner.
    """
    args = []
    for key, value in kwargs.items():
        args.append(('-' if key in ['i', 'o'] else '--') + key)
        if value is not True:
            args.append(str(value))

    cmd = [
        EXECUTABLE,
        *args
    ]

    result = subprocess.run(cmd, cwd=CONTAINER_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if result == 1:
        logger.error('\n'+result.stderr.decode('utf-8'))
    else:
        logger.info('\n'+result.stdout.decode('utf-8'))

    return result