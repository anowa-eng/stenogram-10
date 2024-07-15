from src.alignments import Layer, Alignments
from src.class_register import _registry
from tests.configure_logger import configure_logger
from tests.tools import sample_nodes, reset

test_layer_logger = configure_logger("test_layer")
test_layers_logger = configure_logger("test_layers")

def test_layer():
    """
    Test the functionality of the Layer class.

    This function creates a Layer object with 6 sample nodes using the sample_nodes function.
    It then asserts that the index of the layer is 0.
    The logger is used to log the string representation of the layer.
    Finally, it asserts that the index of each node in the layer is equal to its index in the list of nodes.

    Parameters:
    None

    Returns:
    None
    """
    reset()

    layer = Layer(sample_nodes(6))

    assert layer.id == 0

    test_layer_logger.debug(str(layer))
    
    for i, node in enumerate(layer.nodes):
        assert node.id == i

def test_layers():
    reset()

    test_layers_logger.debug(_registry)

    layers = Alignments(3)

    assert layers.layers[0].id == 0
    assert layers.layers[1].id == 1
    assert layers.layers[2].id == 2

    nodes = sample_nodes(9)

    layers.layers[0].set(nodes[0:3])
    layers.layers[1].set(nodes[3:6])
    layers.layers[2].set(nodes[6:9])

    test_layers_logger.debug(str(layers))

    for i, layer in enumerate(layers.layers):
        assert layer.id == i


def test_translation():
    reset()

    layers = Alignments(3)

    nodes = sample_nodes(9)

    layers.layers[0].set(nodes[0:3])
    layers.layers[1].set(nodes[3:6])
    layers.layers[2].set(nodes[6:9])

    layers.bind(nodes[0], nodes[3])
    layers.bind(nodes[1], nodes[4])
    layers.bind(nodes[2], nodes[5])
    layers.bind(nodes[3], nodes[6])
    layers.bind(nodes[4], nodes[7])
    layers.bind(nodes[5], nodes[8])

    test_layers_logger.debug(str(layers.layers[0].bindings))

    assert layers.output_ids_for_input(nodes[0]) == [3]
    assert layers.input_ids_for_output(nodes[3]) == [0]

    assert layers.output_ids_for_inputs(nodes[0:3]) == [3, 4, 5]
    assert layers.output_ids_for_inputs(nodes[3:6]) == [6, 7, 8]

    assert layers.input_ids_for_outputs(nodes[3:6]) == [0, 1, 2]
    assert layers.input_ids_for_outputs(nodes[6:9]) == [3, 4, 5]

    assert layers.get_output_nodes_for_input(nodes[0]) == [nodes[3]]
    assert layers.get_output_nodes_for_input(nodes[3]) == [nodes[6]]

    assert layers.get_input_nodes_for_output(nodes[3]) == [nodes[0]]
    assert layers.get_input_nodes_for_output(nodes[6]) == [nodes[3]]

    assert layers.get_output_nodes_for_inputs(nodes[0:3]) == nodes[3:6]
    assert layers.get_output_nodes_for_inputs(nodes[3:6]) == nodes[6:9]

    assert layers.get_input_nodes_for_outputs(nodes[3:6]) == nodes[0:3]
    assert layers.get_input_nodes_for_outputs(nodes[6:9]) == nodes[3:6]

    assert layers.get_output_nodes_for_inputs(nodes[0:3], return_respective_lists=True) == [[nodes[3]], [nodes[4]], [nodes[5]]]
    assert layers.get_output_nodes_for_inputs(nodes[3:6], return_respective_lists=True) == [[nodes[6]], [nodes[7]], [nodes[8]]]

    assert layers.get_input_nodes_for_outputs(nodes[3:6], return_respective_lists=True) == [[nodes[0]], [nodes[1]], [nodes[2]]]
    assert layers.get_input_nodes_for_outputs(nodes[6:9], return_respective_lists=True) == [[nodes[3]], [nodes[4]], [nodes[5]]]
    
    # ---------------------------------------------------------------------------- #

    assert layers.translate_down(nodes[0:3], 1) == nodes[3:6]
    assert layers.translate_down(nodes[3:6], 1) == nodes[6:9]

    assert layers.translate_down(nodes[0:3], 1, return_respective_lists=True) == [[nodes[3]], [nodes[4]], [nodes[5]]]

    assert layers.translate_down(nodes[0:3], 2) == nodes[6:9]
    assert layers.translate_down(nodes[0:3], 2, return_respective_lists=True) == [[nodes[6]], [nodes[7]], [nodes[8]]]

    assert layers.translate_up(nodes[6:9], 2) == nodes[0:3]
    assert layers.translate_up(nodes[6:9], 1, return_respective_lists=True) == [[nodes[3]], [nodes[4]], [nodes[5]]]

    assert layers.translate_to_layer(nodes[3:6], 0) == nodes[0:3]
    