from src.alignments.alignments import Layer
from src.rule.selection import SelectionFactory, matches, series
from tests.tools import reset, sample_nodes

reset()
nodes = Layer(sample_nodes(10))

def test_invert_sub():

    does_not_match_k = ~series(['K'], position=2)
    matches_f = matches('F')

    assert isinstance(does_not_match_k, SelectionFactory)

    assert does_not_match_k(nodes).selection == set(range(10))

    assert (does_not_match_k - matches_f)(nodes).selection == {0, 1, 2, 3, 4, 6, 7, 8, 9}

def test_and_or_xor():
    matches_a = matches('A')
    matches_d = matches('D')

    assert (matches_a & matches_d)(nodes).selection == set()
    assert (matches_a | matches_d)(nodes).selection == {0, 3}
    assert (matches_a ^ matches_d)(nodes).selection == {0, 3}

    series_fg = series(['F', 'G'], 1)
    series_efgh = series(['E', 'F', 'G', 'H'])

    assert (series_efgh ^ series_fg)(nodes).selection == {4, 7}
    assert (series_efgh | series_fg)(nodes).selection == {4, 5, 6, 7}
    assert (series_efgh & series_fg)(nodes).selection == {5, 6}
