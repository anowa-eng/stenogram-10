
from src.alignments.alignments import Node, Layer


def sample_nodes(i):
    characters = [chr(i) for i in range(65, 65 + i)]
    return [Node(c) for c in characters]

def reset():
    Node.reset_all_id()
    Layer.reset_all_id()