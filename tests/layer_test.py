from src.layers import Layer, Alignments
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
