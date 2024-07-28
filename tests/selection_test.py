

from src.alignments.alignments import Layer, Node
from src.rule.selection import Selection, matches, series
from tests.tools import reset, sample_nodes


def test_cond():
    reset()

    # Numbered starting from 0.
    layer1 = Layer(sample_nodes(6))

    # Numbered starting from 6.
    layer2 = Layer([
        Node('⅞'),
        Node('Ⅎ⣦'),
        Node(5j + 3),
        Node((1, 2, 3)),
        Node('⋈⒝'),
        *sample_nodes(7),
        Node('⌾K'),
        Node('ḿ'),
        Node('rð'),
        Node('öþ'),
    ])

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    condition_1 = lambda n: n.id % 2 == 0

    assert Selection.select(condition_1, layer1).selection == {0, 2, 4}
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    condition_2 = series(['B', 'C', 'D'])

    assert condition_2(layer1).selection == {1, 2, 3}

    assert (condition_2(layer1) | Selection.select(condition_1, layer1)).selection == {0, 1, 2, 3, 4}
    assert (condition_2(layer1) & Selection.select(condition_1, layer1)).selection == {2}
    assert (condition_2(layer1) ^ Selection.select(condition_1, layer1)).selection == {0, 1, 3, 4}
    assert (condition_2(layer1) - Selection.select(condition_1, layer1)).selection == {1, 3}
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    assert matches('B')(layer1).selection == {1}
    assert matches('D')(layer1).selection == {3}
    assert matches('X')(layer1).selection == set()

    match_b = matches('B')(layer1)
    match_d = matches('D')(layer1)

    assert (match_b | match_d).selection == {1, 3}
    assert (match_b & match_d).selection == set()
    assert (match_b ^ match_d).selection == {1, 3}
    assert (match_b - match_d).selection == {1}
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    test_3a = series(['A', 'B'], position=0)

    assert test_3a(layer1).selection == {0, 1}
    assert test_3a(layer2).selection == set()

    test_3b = series(['C', 'D', 'E'], position=1)

    assert test_3b(layer1).selection == {2, 3, 4}
    assert test_3b(layer2).selection == {13, 14, 15}

    test_3c = series(['E', 'F'], position=2)

    assert test_3c(layer1).selection == {4, 5}
    assert test_3c(layer2).selection == set()

    test_3d = series([5j + 3], position=1)

    assert test_3d(layer1).selection == set()
    assert test_3d(layer2).selection == {8}

    assert test_3c(layer1).selection | test_3b(layer1).selection  == {2, 3, 4, 5}
    assert test_3c(layer1).selection ^ test_3b(layer1).selection  == {2, 3, 5}
    assert test_3c(layer1).selection & test_3b(layer1).selection  == {4}
    assert test_3c(layer1).selection - test_3b(layer1).selection  == {5}

    assert test_3a (layer1).selection | test_3c(layer1).selection | test_3b(layer1).selection  == {0, 1, 2, 3, 4, 5}

    assert (test_3c(layer1) | test_3b(layer1)).selection == {2, 3, 4, 5}
    assert (test_3c(layer1) ^ test_3b(layer1)).selection == {2, 3, 5}
    assert (test_3c(layer1) & test_3b(layer1)).selection == {4}
    assert (test_3c(layer1) - test_3b(layer1)).selection == {5}

