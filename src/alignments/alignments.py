from functools import reduce
import itertools
from typing import List, Mapping, Optional, Sequence, Tuple, TypeAlias, Union

from src.aligner import Aligner
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
        return f'Node(data={self.data}, layer_id={self.id})'

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

    def extend(self, nodes: List[Node]):
        self.nodes.extend(nodes)
        self.set_this_layer_for_all_nodes()

    def insert(self, id, *nodes: List[Node]):
        self.nodes[id:id] = nodes
        self.set_this_layer_for_all_nodes()

    def set(self, nodes: List[Node]):
        self.nodes = nodes
        self.set_this_layer_for_all_nodes()
    
# ---------------------------------------------------------------------------- #

class Bindings:
    '''
    The links between a layer, and the layers directly above and below it.
    '''
    Dictionary: TypeAlias = Mapping[int, List[int]]
    Ungrouped: TypeAlias = List[Tuple[int, int]]

    def __init__(self, anchor: Layer, layer_above: Optional[Layer] = None, layer_below: Optional[Layer] = None):
        '''
        Instantiates a Bindings object.

        Args:
            anchor: The layer which bindings will be bound FROM.
            layer_above: The layer directly above the anchor layer; the parent layer.
            layer_below: The layer directly below the anchor layer; the child layer.
        '''
        if not (layer_above or layer_below):
            raise Exception("Either layer_above or layer_below must be set")

        self.anchor = anchor
        self.layer_above = layer_above
        self.layer_below = layer_below

        self.bindings_up = {}
        self.bindings_down = {}

    def __str__(self):
        str_ = ''
        for k1, vv1 in self.bindings_up.items():
            str_ += f"up: [{', '.join(str(Node.id(v)) for v in vv1)}] <- {Node.id(k1)}\n"
        for k2, vv2 in self.bindings_down.items():
            str_ += (f"down: {Node.id(k2)} -> [{', '.join(str(Node.id(v)) for v in vv2)}]\n")
        return str_

    def check_above(self, output_id: int):
        '''
        Checks that the output node exists in the parent layer.

        Args:
            output_id: The ID of the output node.
        '''
        if not self.layer_above:
            raise TypeError("layer_above is not set")
        
        if not Node.id(output_id) in self.layer_above.nodes:
            raise TypeError(f"Node #{output_id} does not exist in Layer #{self.layer_above.id}")
        
    def check_below(self, output_id: int):
        '''
        Checks that the output node exists in the child layer.

        Args:
            output_id: The ID of the output node.
        '''
        if not self.layer_below:
            raise TypeError("layer_below is not set")
        
        if not Node.id(output_id) in self.layer_below.nodes:
            raise TypeError(f"Node #{output_id} does not exist in Layer #{self.layer_below.id}")
        
    def check_input(self, input_id: int):
        '''
        Checks that the input node exists in the anchor layer.

        Args:
            input_id: The ID of the input node.
        '''
        if not Node.id(input_id) in self.anchor.nodes:
            raise TypeError(f"Node #{input_id} does not exist in Layer #{self.anchor.id}")

    def bind_up(self, input_id: int, output_id: int):
        '''
        Binds an input node in the anchor layer to an output node in the parent layer.
        
        Args:
            input_id: The ID of the input node (the node binding itself to the output).
            output_id: The ID of the output node (the node that is being bound).
        '''

        bindings_logger.debug(f"binding up: {input_id} -> {output_id}")

        self.check_above(output_id)
        self.check_input(input_id)
        
        if input_id not in self.bindings_up:
            self.bindings_up[input_id] = []
        
        if output_id not in self.bindings_up[input_id]:
            self.bindings_up[input_id].append(output_id)

    def bind_down(self, input_id: int, output_id: int):
        '''
        Binds an input node in the anchor layer to an output node in the child layer.
        
        Args:
            input_id: The ID of the input node (the node binding itself to the output).
            output_id: The ID of the output node (the node that is being bound).
        '''

        bindings_logger.debug(f"binding down: {input_id} -> {output_id}")

        self.check_below(output_id)
        self.check_input(input_id)
        
        if input_id not in self.bindings_down:
            self.bindings_down[input_id] = []
        
        if output_id not in self.bindings_down[input_id]:
            self.bindings_down[input_id].append(output_id)

    # -------------------------- Grouping and ungrouping ------------------------- #

    # If node A is bound to nodes B, C, and D, and node E is bound to any of the
    # three nodes B, C, or D, there is an option to automatically include Node E
    # with Node A in a group of input nodes that go to all three nodes
    @staticmethod
    def group(bindings, by_common_singular_inputs=False):
        '''
        Groups a dictionary of bindings into a list of (input_id, output_id) tuples.

        Args:
            bindings: The dictionary of bindings.
            by_common_singular_inputs: If True, all inputs that share any single output will be grouped together.
        '''

        result = {}

        outputs = []
        for output in bindings.values():
            if output not in outputs:
                outputs.append(output)

        # groups the outputs by an input.
        # implemented RECURSIVELY - to prevent errors when changing
        def group_outputs(i) -> None:
            # here's our base case:
            if i == len(outputs):
                return  # stop when reaching the end.

            output = outputs[i]

            def list_contains_number_in_output(lst: Sequence[int]) -> bool:
                return any(
                    num in output
                    for num in lst
                )

            bindings_with_output: dict[int, list[int]] = {
                i: o \
                for i, o in bindings.items()
                if (
                    list_contains_number_in_output(o) # condition
                    if by_common_singular_inputs
                    else (o == output)
                )
            } # inputs that share this output. there has to be at least one.
            print(f'{bindings_with_output=}')

            if by_common_singular_inputs:
                # get ALL the outputs
                output = reduce(
                    lambda a, b: list({ *a, *b }),
                    bindings_with_output.values()
                )

            inputs_sharing_output = []
            # build a tuple with all these input(s)
            for input_ in bindings_with_output:
                inputs_sharing_output.append(input_)
            result[tuple(inputs_sharing_output)] = output
            # convert inputs_sharing-output to a tuple
            # using it as a key

            group_outputs(i + 1)  # keep going

        group_outputs(0)

        return result

    @staticmethod
    def ungroup_bindings(bindings: 'Bindings.Dictionary', is_sorted=True) -> List[Tuple[int, int]]:
        # let's keep this function for now and see if it's useful
        # if it's not we'll remove it later

        '''
        Ungroups a dictionary of bindings into a list of (input_id, output_id) tuples.

        Args:
            bindings: The dictionary of bindings.
            is_sorted: Whether the dictionary should be sorted.
        '''
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

# ---------------------------------------------------------------------------- #

class Alignments:
    '''
    Alignments is a list of layers, where each layer is a list of nodes.

    It is used to store the bindings that connect nodes to and from each other in different layers.
    '''
    def __init__(self, num_layers_or_layers_list: Union[int, List[Layer]]):
        '''
        Instantiates an Alignments object.

        Args:
            num_layers_or_layers_list: The number of blank layers to create, or a list of layers that will be set.
        '''
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
    
    # -------------------------------- Add a layer ------------------------------- #

    def add_layer(self):
        '''
        Adds a new blank layer to the end of the list of layers.
        '''
        self.layers.append(Layer([]))
        self.layers[-2].bindings.layer_below = self.layers[-1]

        self.layers[-1].bindings = Bindings(
            anchor=self.layers[-1],
            layer_above=self.layers[-2]
        )

    # ---------------- Instantiate alignments from aligner output ---------------- #

    # Helper functions

    @staticmethod
    def _from_aligner_word(aligner_output: Aligner.Word) -> 'Alignments':
        '''
        Instantiates an Alignments object from the output of a single word that was run through the Aligner.

        Args:
            aligner_output: A single item from the output of an m2m-aligner run.
        '''

        # TODO (after detox): Add support for multiple aligner outputs

        alignments = Alignments(2) # two layers from grapheme -> phoneme

        nodes = zip(*aligner_output)

        for (graphemes, phonemes) in nodes:
            g_nodes = [Node(g) for g in graphemes]
            p_nodes = [Node(p) for p in phonemes if p != '_']
            alignments.layers[0].extend(g_nodes)
            alignments.layers[1].extend(p_nodes)

            # Bind the nodes to each other
            for g in g_nodes:
                for p in p_nodes:
                    alignments.bind(g, p)

        return alignments

    @staticmethod
    def _from_aligner_output(aligner_output: Aligner.Output) -> 'Alignments':
        '''
        Instantiates an Alignments object from the output of an m2m-aligner run.

        Args:
            aligner_output: The output of an m2m-aligner run.
        '''
        aligner_output = [Alignments._from_aligner_word(w) for w in aligner_output]
        return aligner_output

    # Public methods
    
    @staticmethod
    def from_phrase(phrase: str) -> 'Alignments':
        '''
        Instantiates an Alignments object from a phrase.

        Args:
            phrase: The phrase to be aligned.
        '''
        aligner_output = Aligner.align(phrase)
        return Alignments._from_aligner_output(aligner_output)
    
    @staticmethod
    def from_word(word: str) -> 'Alignments':
        '''
        Instantiates an Alignments object from a word.

        Args:
            word: The word to be aligned.
        '''
        aligner_output = Aligner.align(word)
        return Alignments._from_aligner_output(aligner_output)[0]

    # ---------------------------------------------------------------------------- #

    def bind_id(self, input_id: int, output_id: int):
        '''
        Binds an input node in its to an output node in another layer.
        
        The layers must be adjacent to each other and inside the list of layers that is set in the Alignments object.
        
        Args:
            input_id: The ID of the input node (the node binding itself to the output).
            output_id: The ID of the output node (the node that is being bound).
        '''
        input_layer = Node.id(input_id).layer
        output_layer = Node.id(output_id).layer

        # Check that the layers are adjacent.
        # -1 = above, 1 = below
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
        '''
        A shortcut for binding an input node in its to an output node in another layer.

        Args:
            input_node: The input node (the node binding itself to the output).
            output_node: The output node (the node that is being bound).
        '''
        self.bind_id(input_node.id, output_node.id)


    # ------------------------- Traversing the alignments ------------------------ #

    def output_ids_for_input(self, node: Node) -> List[int]:
        '''
        Returns the IDs of the output nodes that are bound to the input node.

        Args:
            node: The input node.

        Returns:
            List[int]: A list of output node IDs.
        '''
        layer = node.layer

        if not layer:
            raise TypeError('Node is not within a Layer')

        if not layer.bindings.layer_below:
            raise Exception('Input node is at the last layer. Cannot traverse any further.')
        
        return layer.bindings.bindings_down[node.id]
    
    def input_ids_for_output(self, node: Node) -> List[int]:
        '''
        Returns the IDs of the input nodes that are bound to the output node.

        Args:
            node: The output node.

        Returns:
            List[int]: A list of output node IDs.
        '''
        layer = node.layer

        if not layer:
            raise TypeError('Node is not within a Layer')
        
        if not layer.bindings.layer_above:
            raise Exception('Output node is at the first layer. Cannot traverse any further.')
        
        return layer.bindings.bindings_up[node.id]
    
    def output_ids_for_inputs(self, nodes: Sequence[Node], return_respective_lists=False) -> Union[List[int], List[List[int]]]:
        """
        Returns a list of output node IDs for a given list of input nodes.

        Args:
            nodes (Sequence[Node]): The list of input nodes.
            return_respective_lists (bool, optional): If True, the function will return a list of lists, where each sublist
                contains the output node IDs corresponding to the input node. If False, the function
                will return a single list of output node IDs. Defaults to False.

        Returns:
            List[int]: A list of output node IDs.
            List[List[int]]: In a special case where return_respective_lists is True, a list of lists of output node IDs.

        Raises:
            TypeError: If an input node is not within a Layer.
            Exception: If an output node is at the first layer and cannot traverse any further.
        """
        ids = []
        for node in nodes:
            (ids.append if return_respective_lists else ids.extend)(self.output_ids_for_input(node))
        if not return_respective_lists:
            ids.sort()
        return ids
    
    def input_ids_for_outputs(self, nodes: Sequence[Node], return_respective_lists=False) -> Union[List[int], List[List[int]]]:
        """
        Returns a list of input node IDs for a given list of output nodes.

        Args:
            nodes (Sequence[Node]): The list of output nodes.
            return_respective_lists (bool, optional): If True, the function will return a list of lists, where each sublist
                contains the input node IDs corresponding to the output node. If False, the function
                will return a single list of input node IDs. Defaults to False.

        Returns:
            List[int]: A list of output node IDs.
            List[List[int]]: In a special case where return_respective_lists is True, a list of lists of output node IDs.

        Raises:
            TypeError: If an output node is not within a Layer.
            Exception: If an input node is at the last layer and cannot traverse any further.
        """
        ids = []
        for node in nodes:
            (ids.append if return_respective_lists else ids.extend)(self.input_ids_for_output(node))
        if not return_respective_lists:
            ids.sort()
        return ids
    
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def get_output_nodes_for_input(self, node: Node) -> List[Node]:
        """
        Returns a list of output nodes corresponding to the given input node.

        Args:
            node (Node): The input node.

        Returns:
            List[Node]: A list of nodes.
        
        Raises:
            TypeError: If an output node is not within a Layer.
            Exception: If an input node is at the last layer and cannot traverse any further.
        """
        return [Node.id(i) for i in self.output_ids_for_input(node)]
    
    def get_input_nodes_for_output(self, node: Node) -> List[Node]:
        """
        Returns a list of input node IDs corresponding to the given output node.

        Args:
            node (Node): The output node.

        Returns:
            List[Node]: A list of input node IDs.

        Raises:
            TypeError: If an output node is not within a Layer.
            Exception: If an input node is at the last layer and cannot traverse any further.
        """
        return [Node.id(i) for i in self.input_ids_for_output(node)]
    
    def get_output_nodes_for_inputs(self, nodes: Sequence[Node], return_respective_lists=False) -> Union[List[Node], List[List[Node]]]:
        """
        Returns a list of output nodes for a given list of input nodes.

        Args:
            nodes (Sequence[Node]): The list of input nodes.
            return_respective_lists (bool): Whether to return the output nodes as separate lists.

        Returns:
            List[Node]: A list of output nodes.
            List[List[Node]]: In a special case where return_respective_lists is True, a list of lists of output nodes.

        Raises:
            TypeError: If an output node is not within a Layer.
            Exception: If an input node is at the last layer and cannot traverse any further.
        """
        result = []
        for node in nodes:
            (result.append if return_respective_lists else result.extend)(self.get_output_nodes_for_input(node))
        if not return_respective_lists:
            result.sort(key=lambda x: x.id)
        return result
    
    def get_input_nodes_for_outputs(self, nodes: Sequence[Node], return_respective_lists=False) -> Union[List[Node], List[List[Node]]]:
        """
        Returns a list of input nodes for a given list of output nodes.

        Args:
            nodes (Sequence[Node]): The list of output nodes.
            return_respective_lists (bool): Whether to return the input nodes as separate lists.

        Returns:
            List[Node]: A list of input nodes.
            List[List[Node]]: In a special case where return_respective_lists is True, a list of lists of input nodes.

        Raises:
            TypeError: If an input node is not within a Layer.
            Exception: If an output node is at the last layer and cannot traverse any further.
        """
        result = []
        for node in nodes:
            (result.append if return_respective_lists else result.extend)(self.get_input_nodes_for_output(node))
        if not return_respective_lists:
            result.sort(key=lambda x: x.id)
        return result

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    
    def translate_down(self, nodes: Sequence[Node], amount: int, return_respective_lists=False) -> Union[List[Node], List[List[Node]]]:
        """
        Translates a list of nodes down by a given amount.

        Args:
            nodes (Sequence[Node]): The list of nodes to translate.
            amount (int): The amount to translate by.
            return_respective_lists (bool): Whether to return the translated nodes as separate lists.

        Returns:
            List[Node]: A list of translated nodes.
            List[List[Node]]: In a special case where return_respective_lists is True, a list of lists of translated nodes.

        Raises:
            TypeError: If an input or output node is not within a Layer.
            Exception: If an input node is at the last layer and cannot traverse any further.
        """
        if amount == 0:
            return nodes
        output_nodes = self.get_output_nodes_for_inputs(nodes, return_respective_lists=return_respective_lists)
        if return_respective_lists:
            return [self.translate_down(o, amount - 1) for o in output_nodes]
        else:
            return self.translate_down(output_nodes, amount - 1)
    
    def translate_up(self, nodes: Sequence[Node], amount: int, return_respective_lists=False) -> Union[List[Node], List[List[Node]]]:
        """
        Translates a list of nodes up by a given amount.

        Args:
            nodes (Sequence[Node]): The list of nodes to translate.
            amount (int): The amount to translate by.
            return_respective_lists (bool): Whether to return the translated nodes as separate lists.

        Returns:
            List[Node]: A list of translated nodes.
            List[List[Node]]: In a special case where return_respective_lists is True, a list of lists of translated nodes.

        Raises:
            TypeError: If an input or output node is not within a Layer.
            Exception: If an input node is at the last layer and cannot traverse any further.
        """
        if amount == 0:
            return nodes
        input_nodes = self.get_input_nodes_for_outputs(nodes, return_respective_lists=return_respective_lists)
        if return_respective_lists:
            return [self.translate_up(i, amount - 1) for i in input_nodes]
        else:
            return self.translate_up(input_nodes, amount - 1)
    
    def translate_to_layer(self, nodes: Sequence[Node], layer_number: int, return_respective_lists=False) -> Union[List[Node], List[List[Node]]]:
        all_layer_ids = [layer.id for layer in self.layers]
        respective_lists = []

        for node in nodes:
            idx = all_layer_ids.index(node.layer.id)

            translate = (self.translate_down if idx < layer_number else self.translate_up)
            amount = abs(idx - layer_number)

            respective_lists.append(translate([node], amount))
        
        if return_respective_lists:
            return respective_lists
        else:
            return list(itertools.chain(*respective_lists))

# TODO 07/06/2024: finish this
