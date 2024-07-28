import asyncio
from src.aligner5.aligner import align_text
from src.aligner5.word import Word
from src.alignments import Alignments, Bindings, Layer, Node

# ---------------------------------------------------------------------------- #
#                          Create alignments from word                         #
# ---------------------------------------------------------------------------- #

def alignments_from_word(word: Word) -> Alignments:
    if word.alignments:
        alignments = Alignments(2)

        graphemes, phonemes = word.alignments

        for grapheme_collection, phoneme_collection in zip(graphemes, phonemes):
            print(grapheme_collection, phoneme_collection)

            g_nodes = [Node(grapheme) for grapheme in grapheme_collection]
            p_nodes = [Node(phoneme) for phoneme in phoneme_collection]

            alignments.layers[0].extend(g_nodes)
            alignments.layers[1].extend(p_nodes)

            # Bind the nodes to each other
            for g in g_nodes:
                for p in p_nodes:
                    alignments.bind(g, p)
    
        return alignments
    
    else:
        raise ValueError("Word does not have alignments.")

def alignments_from_words(words: list[Word]) -> Alignments:
    return [alignments_from_word(word) for word in words]

# ---------------------------------------------------------------------------- #

def get_node_ids(ids: list[int]) -> list[Node]:
    return tuple(Node.id(id) for id in ids)

def node_bindings_down(layer: Layer) -> str:
    grouped_bindings = Bindings.group(layer.bindings.bindings_down)

    grouped_bindings = {
        get_node_ids(k): get_node_ids(v) \
            for k, v in grouped_bindings.items()
    }
    return grouped_bindings

# ---------------------------------------------------------------------------- #
#                   Formatting alignments in a compact manner                  #
# ---------------------------------------------------------------------------- #

def compact_fmt_node_groups(nodes: tuple[Node]) -> str:
    # for a single string of nodes
    return '|'.join([':'.join([node.data for node in collection_g]) for collection_g in nodes])

def compact_layer_str(layer: Layer) -> str:
    # for a single layer
    node_bindings_down_ = node_bindings_down(layer)

    graphemes = compact_fmt_node_groups(node_bindings_down_.keys())
    phonemes = compact_fmt_node_groups(node_bindings_down_.values())

    return f'(layer #{layer.id}) {graphemes}\t-> (layer #{layer.id + 1}) {phonemes}'

def compact_alignments_str(alignments: Alignments) -> str:
    # for an Alignments object, not including the last layer
    return '\n'.join(compact_layer_str(layer) for layer in alignments.layers[:-1])
    