from re import L
from typing import List, Mapping, Optional, Tuple, TypeAlias, Union

from src.class_register import IndexedClass, indexed
from tests.configure_logger import configure_logger

bindings_logger = configure_logger("bindings")

class Node(IndexedClass['Node']):
    '''
    A single node in a layer.
    '''
    @indexed
    def __init__(self, data) -> None:
        self.data = data
        self.layer: Optional['Layer'] = None

    def __repr__(self):
        return f'Node(data={self.data}, layer={self.layer}, layer_id={self.id})'
    
    def __str__(self):
        str_ = f"Node({self.data})"
        if self.layer:
            str_ += f" @ "
            if self.layer.id != -1:
                str_ += f"layer {self.layer.id}"
            str_ += f", id {self.id}"
        return str_

class Layer(IndexedClass['Layer']):
    '''
    A layer of nodes.
    '''
    @indexed
    def __init__(self, nodes: List[Node]):
        self.nodes = nodes
        self.bindings: Optional[Bindings] = None

    def __repr__(self):
        return f'Layer(nodes={self.nodes}, id={self.id})'
    
    def __str__(self):
        nodes = '\n  ' + ",\n  ".join([str(n) for n in self.nodes])
        return f"Layer #{self.id}: [{nodes}\n]"

    # ---------------------------------------------------------------------------- #

    def set_this_layer_for_all_nodes(self):
        for node in self.nodes:
            if not node.layer:
                node.layer = self

    def append(self, node: Node):
        self.nodes.append(node)
        self.set_this_layer_for_all_nodes()

    def insert(self, id, *nodes: List[Node]):
        self.nodes[id:id] = nodes
        self.set_this_layer_for_all_nodes()

    def set(self, nodes: List[Node]):
        self.nodes = nodes
        self.set_this_layer_for_all_nodes()
    
# ---------------------------------------------------------------------------- #

class Bindings:
    Dictionary: TypeAlias = Mapping[int, List[int]]
    Ungrouped: TypeAlias = List[Tuple[int, int]]

    def __init__(self, anchor: Layer, layer_above: Optional[Layer] = None, layer_below: Optional[Layer] = None):
        if not (layer_above or layer_below):
            raise Exception("Either layer_above or layer_below must be set")

        self.anchor = anchor
        self.layer_above = layer_above
        self.layer_below = layer_below

        self.bindings_up = {}
        self.bindings_down = {}

    def check_above(self, output_id: int):
        if not self.layer_above:
            raise TypeError("layer_above is not set")
        
        if not Node.id(output_id) in self.layer_above.nodes:
            raise TypeError(f"Node #{output_id} does not exist in Layer #{self.layer_above.id}")
        
    def check_below(self, output_id: int):
        if not self.layer_below:
            raise TypeError("layer_below is not set")
        
        if not Node.id(output_id) in self.layer_below.nodes:
            raise TypeError(f"Node #{output_id} does not exist in Layer #{self.layer_below.id}")
        
    def check_input(self, input_id: int):
        if not Node.id(input_id) in self.anchor.nodes:
            raise TypeError(f"Node #{input_id} does not exist in Layer #{self.anchor.id}")

    def bind_up(self, input_id: int, output_id: int):
        bindings_logger.debug(f"binding up: {input_id} -> {output_id}")

        self.check_above(output_id)
        self.check_input(input_id)
        
        if input_id not in self.bindings_up:
            self.bindings_up[input_id] = []
        
        if output_id not in self.bindings_up[input_id]:
            self.bindings_up[input_id].append(output_id)

    def bind_down(self, input_id: int, output_id: int):
        bindings_logger.debug(f"binding down: {input_id} -> {output_id}")

        self.check_below(output_id)
        self.check_input(input_id)
        
        if input_id not in self.bindings_down:
            self.bindings_down[input_id] = []
        
        if output_id not in self.bindings_down[input_id]:
            self.bindings_down[input_id].append(output_id)


# ---------------------------------------------------------------------------- #

class Layers:
    def __init__(self, num_layers_or_layers_list: Union[int, List[Layer]]):
        match type(num_layers_or_layers_list).__name__:
            case 'list':
                self.layers = num_layers_or_layers_list
            case 'int':
                self.layers = [Layer([]) for _ in range(num_layers_or_layers_list)]
            case _:
                raise TypeError(f"num_layers_or_layers_list must be int or list, not {type(num_layers_or_layers_list)}")
        
        for i, l in enumerate(self.layers):
            l.set_this_layer_for_all_nodes()

            idx = self.layers.index(l)
            bindings = Bindings(
                anchor=l,
                layer_above=self.layers[idx - 1] if i > 0 else None,
                layer_below=self.layers[idx + 1] if i < len(self.layers) - 1 else None)

            l.bindings = bindings

    def __repr__(self):
        return f'Layers({self.layers})'
    
    def _repr_indent(self, str_: str, spaces: int):
        return "\n".join([chr(32) * spaces + s for s in str_.split("\n")])
    def __str__(self):
        layer_strs = [('\n' + str(l)) for l in self.layers]
        layer_strs = [self._repr_indent(s, 2) for s in layer_strs]
        return f"Layers: [\n" + '\n'.join(layer_strs) + "\n]"
    
    # ---------------------------------------------------------------------------- #

    def bind_id(self, input_id: int, output_id: int):
        input_layer = Node.id(input_id).layer
        output_layer = Node.id(output_id).layer

        above_or_below = self.layers.index(output_layer) - self.layers.index(input_layer)

        bindings_logger.debug(f"LAYERS.BIND CALL: {input_id} -> {output_id} ({above_or_below})")

        if above_or_below == -1:
            input_layer.bindings.bind_up(input_id, output_id)
            output_layer.bindings.bind_down(output_id, input_id)
        elif above_or_below == 1:
            input_layer.bindings.bind_down(input_id, output_id)
            output_layer.bindings.bind_up(output_id, input_id)
        else:
            raise TypeError(f"Layers #{input_layer.id}, containing Node #{input_id}, and #{output_layer.id}, containing Node #{output_id}, are not adjacent")

    def bind(self, input_node: Node, output_node: Node):
        self.bind_id(input_node.id, output_node.id)

    # ---------------------------------------------------------------------------- #

    def ungroup_bindings(self, bindings: Bindings.Dictionary, is_sorted=True):
        result = []

        sorted_bindings = {}
        if is_sorted:
            for input_id, output_ids in sorted(bindings.items(), key=lambda x: x[0]):
                output_ids.sort()
                sorted_bindings[input_id] = output_ids
            bindings = sorted_bindings

        for input_id, output_ids in bindings.items():
            result.extend((input_id, o) for o in output_ids)
        
        return result

    # If node A is bound to nodes B, C, and D, and node E is bound to any of the
    # three nodes B, C, or D, there is an option to automatically include Node E
    # with Node A in a group of input nodes that go to all three nodes
    def group_bindings_with_common_outputs(self,
        bindings: Bindings.Dictionary | Bindings.Ungrouped,
        group_common_inputs: bool = False
    ):
        if type(bindings) not in [dict, list]:
            raise TypeError(f'bindings can only be of type dict or list, not {type(bindings)}')

        if isinstance(bindings, dict):
            bindings = self.ungroup_bindings(bindings)
        
        for i, binding in enumerate(bindings):
            print(binding)

    # ---------------------------------------------------------------------------- #

    def _inputs_for_outputs_indices(self):
        if len(self.bindings):
            groups = [[self.bindings[0]]]
            for i, (input_node_idx, output_node_idx) in enumerate(self.ungroup_bindings(self.bindings))[1:]:
                prev_i_idx, prev_o_idx = self.bindings[i - 1]
                has_same_input = input_node_idx == prev_i_idx
                has_same_output = output_node_idx == prev_o_idx

                if not (has_same_input or has_same_output):
                    groups.append([])
                groups[-1].append((input_node_idx, output_node_idx))
            
            return groups
        else:
            return [[]]
    

# TODO 07/06/2024: finish this
