from dataclasses import dataclass, field
from typing import Callable, List, Union
from src.alignments.alignments import Layer, Node

# ---------------------------------------------------------------------------- #
#                     Selection class and related functions                    #
# ---------------------------------------------------------------------------- #

# ----------------------------------- Class ---------------------------------- #

TwoArgumentCondition = Callable[[int, List[Node]], bool]
SingleArgumentCondition = Callable[[List[Node]], bool]

Condition = Union[TwoArgumentCondition, SingleArgumentCondition]

@dataclass
class Selection:
    '''
    Stores a set of indices that correspond to nodes in a layer that have been selected.
    '''
    layer: Layer
    selection: field(default=set())

    def __str__(self) -> str:
        return f'Selection for Layer #{self.layer.id}: {self.selection}'
    
    # -------------- Set intersection, union, difference, symmetric -------------- #
    # -------------------- difference, etc. are all available. ------------------- #

    def __and__(self, other: 'Selection') -> 'Selection':
        return Selection(self.layer, self.selection & other.selection)

    def __or__(self, other: 'Selection') -> 'Selection':
        return Selection(self.layer, self.selection | other.selection)

    def __sub__(self, other: 'Selection') -> 'Selection':
        return Selection(self.layer, self.selection - other.selection)

    def __xor__(self, other: 'Selection') -> 'Selection':
        return Selection(self.layer, self.selection ^ other.selection)

    # ---------------------------- Running a condition --------------------------- #

    def select(condition: Condition, layer: Layer) -> bool:
        '''
        Runs a condition on all nodes in the layer and returns the selection.'''
        nodes = layer.nodes

        if condition.__code__.co_argcount == 1:
            return Selection(layer, { node.id for node in nodes if condition(node) })
        else:
            return Selection(layer, { node.id for i, node in enumerate(nodes) if condition(i, nodes) })
        
# ---------------------------------------------------------------------------- #
#                            SelectionFactory class                            #
# ---------------------------------------------------------------------------- #

@dataclass
class SelectionFactory:
    '''
    Factory class for creating Selection objects.
    '''

    condition: Callable[[Layer], Selection]

    def __call__(self, layer: Layer) -> Selection:
        return self.condition(layer)
    
    def __str__(self) -> str:
        return f'SelectionFactory: {self.condition}'
    
    # ---------------------------------------------------------------------------- #

    def __and__(self, other: 'SelectionFactory') -> 'SelectionFactory':
        return SelectionFactory(lambda layer: self(layer) & other(layer))
    
    def __or__(self, other: 'SelectionFactory') -> 'SelectionFactory':
        return SelectionFactory(lambda layer: self(layer) | other(layer))
    
    def __sub__(self, other: 'SelectionFactory') -> 'SelectionFactory':
        return SelectionFactory(lambda layer: self(layer) - other(layer))
    
    def __xor__(self, other: 'SelectionFactory') -> 'SelectionFactory':
        return SelectionFactory(lambda layer: self(layer) ^ other(layer))
    
    def __invert__(self, other: 'SelectionFactory') -> 'SelectionFactory':
        return SelectionFactory(lambda layer: ~(self(layer)))
    
# --------------------------------- Functions -------------------------------- #

INITIAL = 0
MEDIAL = 1
FINAL = 2

def series(values: List, position: int = -1) -> Selection:
    def wrapper(layer: Layer) -> bool:

        selection = set()
        single_series = set()

        final_node = layer.nodes[-1]

        nodes = layer.nodes[1:-1] if position == MEDIAL else layer.nodes

        for node in nodes:
            i = len(single_series)
            if node.data == values[i]:
                single_series.add(node.id)

                if i == len(values) - 1:
                    if position == FINAL:
                        if final_node.id in single_series:
                            selection |= single_series
                    else:
                        selection |= single_series
                    single_series.clear()
            else:
                if position == INITIAL:
                    break
                single_series.clear()
        
        return Selection(layer, selection)

    return wrapper

def matches(value) -> Selection:
    def wrapper(layer: Layer) -> bool:
        return Selection.select(lambda node: node.data == value, layer)
    
    return wrapper
