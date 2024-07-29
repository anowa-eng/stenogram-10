from src.alignments.alignments import Bindings, Layer, Alignments
from src.class_register import _registry
from tests.configure_logger import configure_logger
from tests.tools import sample_nodes, reset


logger = configure_logger("test_bindings")

def test_one_to_one_bindings():
    reset()

    a, b, c, d, e, f, g, h, i, j, k, l = sample_nodes(12)

    layers = Alignments(4)

    layers.layers[0].set([a, b, c])
    layers.layers[1].set([d, e, f])
    layers.layers[2].set([g, h, i])
    layers.layers[3].set([j, k, l])

    logger.debug(layers)

    assert layers.layers[0].nodes[0] == a
    assert layers.layers[1].nodes[1] == e
    assert layers.layers[2].nodes[2] == i

    # ---------------------------------------------------------------------------- #)

    logger.debug(layers)

    assert layers.layers[0].bindings.anchor is layers.layers[0]
    assert layers.layers[1].bindings.anchor is layers.layers[1]
    assert layers.layers[2].bindings.anchor is layers.layers[2]
    assert layers.layers[3].bindings.anchor is layers.layers[3]

    assert layers.layers[0].bindings.layer_above is None
    assert layers.layers[1].bindings.layer_above is layers.layers[0]
    assert layers.layers[2].bindings.layer_above is layers.layers[1]
    assert layers.layers[3].bindings.layer_above is layers.layers[2]

    assert layers.layers[0].bindings.layer_below is layers.layers[1]
    assert layers.layers[1].bindings.layer_below is layers.layers[2]
    assert layers.layers[2].bindings.layer_below is layers.layers[3]
    assert layers.layers[3].bindings.layer_below is None

    # ---------------------------------------------------------------------------- #)

    # Let's create a single binding between nodes a and d.
    # The nodes should be in adjacent layers.

    layers.bind_id(a.id, d.id)
    layers.bind_id(g.id, d.id) # a <-> d <-> g

    assert layers.layers[0].bindings.bindings_up == {}
    assert layers.layers[0].bindings.bindings_down == {a.id: [d.id]}

    assert layers.layers[1].bindings.bindings_up == {d.id: [a.id]}
    assert layers.layers[1].bindings.bindings_down == {d.id: [g.id]}
    
    assert layers.layers[2].bindings.bindings_up == {g.id: [d.id]}
    assert layers.layers[2].bindings.bindings_down == {}

    layers.bind_id(g.id, d.id) # already been bound
    
    assert layers.layers[1].bindings.bindings_up == {d.id: [a.id]}
    assert layers.layers[1].bindings.bindings_down == {d.id: [g.id]}
    
    assert layers.layers[2].bindings.bindings_up == {g.id: [d.id]}
    assert layers.layers[2].bindings.bindings_down == {}

    layers.bind_id(g.id, j.id)

    layers.bind_id(b.id, e.id)
    layers.bind_id(e.id, h.id)
    layers.bind_id(h.id, k.id)

    layers.bind_id(c.id, f.id)
    layers.bind_id(f.id, i.id)
    layers.bind_id(i.id, l.id)

    # 0     1     2     3
    # a <-> d <-> g <-> j
    # b <-> e <-> h <-> k
    # c <-> f <-> i <-> l

    assert layers.layers[0].bindings.bindings_up == {}
    assert layers.layers[0].bindings.bindings_down == {a.id: [d.id], b.id: [e.id], c.id: [f.id]}

    assert layers.layers[1].bindings.bindings_up == {d.id: [a.id], e.id: [b.id], f.id: [c.id]}
    assert layers.layers[1].bindings.bindings_down == {d.id: [g.id], e.id: [h.id], f.id: [i.id]}

    assert layers.layers[2].bindings.bindings_up == {g.id: [d.id], h.id: [e.id], i.id: [f.id]}
    assert layers.layers[2].bindings.bindings_down == {g.id: [j.id], h.id: [k.id], i.id: [l.id]}

    assert layers.layers[3].bindings.bindings_up == {j.id: [g.id], k.id: [h.id], l.id: [i.id]}
    assert layers.layers[3].bindings.bindings_down == {}

def test_one_to_many_bindings():
    a, b, c, d, e, f = sample_nodes(6)

    layers = Alignments([
        Layer([a, b, c]),
        Layer([d, e, f])
    ])

    logger.debug(a)
    logger.debug(d)

    assert layers.layers[0].bindings.layer_above is None
    assert layers.layers[1].bindings.layer_above is layers.layers[0]

    assert layers.layers[0].bindings.layer_below is layers.layers[1]
    assert layers.layers[1].bindings.layer_below is None

    layers.bind(a, d)
    layers.bind(b, d)
    layers.bind(c, e)
    layers.bind(c, f)

    assert layers.layers[0].bindings.bindings_up == {}
    assert layers.layers[0].bindings.bindings_down == {a.id: [d.id], b.id: [d.id], c.id: [e.id, f.id]}

    assert layers.layers[1].bindings.bindings_up == {d.id: [a.id, b.id], e.id: [c.id], f.id: [c.id]}
    assert layers.layers[1].bindings.bindings_down == {}

# ---------------------------------------------------------------------------- #
#                              ungrouping bindings                             #
# ---------------------------------------------------------------------------- #

def test_grouping():
    reset()

    a, b, c, d, e, f, g, h, i = sample_nodes(9)

    layers = Alignments([
        Layer([a, b, c]),
        Layer([d, e, f]),
        Layer([g, h, i])

    ])

    layers.bind(a, d)
    layers.bind(b, d)
    layers.bind(c, e)
    layers.bind(c, f)

    layers.bind(d, g)
    layers.bind(e, h)
    layers.bind(f, i)

    assert layers.output_ids_for_input(d) == [g.id]
    assert layers.input_ids_for_output(g) == [d.id]

    bindings_down = layers.layers[0].bindings.bindings_down
    assert Bindings.group(bindings_down, by_common_singular_inputs=True) \
        == {(a.id, b.id): [d.id],
            (c.id,): [e.id, f.id]}
