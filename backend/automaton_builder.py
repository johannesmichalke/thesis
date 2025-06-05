# automaton_builder.py
from collections import deque
from copy import deepcopy
from math import floor

from ast_nodes import *
import itertools
import libmata.nfa.nfa as mata_nfa
from libmata.alphabets import *

from visual_cleanup import relabel_and_aggregate, int_to_lsbf

config = mata_nfa.store()

def setup(k):
    global config
    a = OnTheFlyAlphabet()
    # a = IntAlphabet(0, 2**k - 1)
    # we need every integer symbol {0,1,…,2**k-1} in its map
    a.add_symbols_for_names([ str(i) for i in range(2**k) ])
    #print(f"alphabet: {a.get_alphabet_symbols()}")
    config['alphabet'] = a

def build_automaton(node) -> (mata_nfa.Nfa, [str]):
    global config
    if isinstance(node, LessEqual):
        # Atomic case: build automaton for t <= u
        aut, variables = build_atomic_automaton(node)
        # print(aut.to_dot_str())
        # aut = project_variable(aut, 0 )
        #print(f"automaton for {node}:")
        #print(aut.to_dot_str())
        return aut, variables

    elif isinstance(node, Or):
        left_automaton, left_variables = build_automaton(node.left)
        right_automaton, right_variables = build_automaton(node.right)
        aut, variables = union(left_automaton, right_automaton, left_variables, right_variables)
        #print(f"automaton for {node}:")
        #print(aut.to_dot_str())
        return aut, variables

    elif isinstance(node, Not):
        child_automaton, variables = build_automaton(node.expr)
        #child_automaton = mata_nfa.minimize(child_automaton)
        #print(f"child automaton: {child_automaton.to_dot_str()}")
        if not is_deterministic(child_automaton):
            #print("Child automaton is not deterministic, determinizing...")
            child_automaton = determinize(child_automaton)
            #print(f"determinized automaton \n: {child_automaton.to_dot_str()}")
        #child_automaton = mata_nfa.complement(child_automaton, config['alphabet'])
        child_automaton = complete(child_automaton, variables)
        #print(f"completed automaton \n: {child_automaton.to_dot_str()}")
        child_automaton = complement(child_automaton)
        #print(f"complemented automaton \n: {child_automaton.to_dot_str()}")
        #child_automaton = mata_nfa.complement(child_automaton, alphabet = config['alphabet'])
        #print(f"child automaton: {child_automaton.to_dot_str()}")
        #print(f"automaton for {node}:")
        #print(child_automaton.to_dot_str())
        return child_automaton, variables

    elif isinstance(node, Exists):
        child_automaton, variables = build_automaton(node.formula)
        setup(len(variables) - 1)
        index = variables.index(node.var)
        #print(f"automaton for {node}:")
        aut, variables = project_variable(child_automaton, index, variables)
        #print(aut.to_dot_str())
        return aut, variables

    else:
        raise ValueError(f"Unsupported node type in build_automaton: {type(node)}")


def project_variable(aut : mata_nfa.Nfa , index, variables):
    # This function will project the variable out of the automaton
    # You will need to implement this based on your automata library
    # for each transistion, do calculation
    transitions = aut.get_trans_as_sequence()
    states = aut.get_reachable_states()
    initial_states = aut.initial_states
    final_states = set(aut.final_states)
    #print(f"final states: {final_states}")
    new_aut = mata_nfa.Nfa()
    for state in states:
        new_aut.add_state(state)
    new_aut.initial_states = initial_states
    for transition in transitions:
        source = transition.source
        target = transition.target
        symbol = transition.symbol
        new_symbol = symbol % 2**index + ((symbol - symbol % 2**(index+1)) // 2)
        #print(f"Replaced {symbol} with {new_symbol} from {source} to {target}")
        new_aut.add_transition(source, new_symbol, target)
    transitions = new_aut.get_trans_as_sequence()
    workset = deepcopy(final_states)
    visited = set()
    #print(f"final states: {final_states}")
    while workset:
        #print(f"looping with {workset}")
        state = workset.pop()
        for transition in transitions:
            if transition.target == state:
                source = transition.source
                symbol = transition.symbol
                if symbol == 0 and source not in visited:
                    final_states.add(source)
                    workset.add(source)
                    visited.add(source)
    #print(f"final states: {final_states}")
    new_aut.final_states = final_states
    #print(f"Projection done.")
    del variables[index]
    return new_aut, variables

def build_atomic_automaton(node):
    # This function will build an automaton for the atomic case
    # You will need to implement this based on your automata library
    b, map = count_tree(node)
    x = []
    a = []
    n = len(map)
    setup(n)
    for var in map.keys():
        x.append(var)
        a.append(map.get(var))
    #print(f"b: {b}, x: {x}, a: {a}")
    aut = mata_nfa.Nfa()
    sb = aut.add_state(encode(b))
    if b >= 0:
        final_states = {sb}
    else:
        final_states = set()
    aut.initial_states = {sb}
    states = {sb}
    worklist = deque()
    worklist.append(sb)
    while worklist:
        state = worklist.popleft()
        for zeta in itertools.product([0, 1], repeat=n):
            k = decode(state)
            dotproduct = sum(zeta[i] * a[i] for i in range(n))
            j = floor((k - dotproduct) / 2)
            if encode(j) not in states:
                sj = aut.add_state(encode(j))
                if j >= 0:
                    final_states.add(sj)
                worklist.append(sj)
                states.add(sj)
            else:
                sj = encode(j)
            aut.add_transition(state, lsbf_to_int(zeta), sj)
    aut.final_states = final_states
    #print("finished")
    return aut, x


def union_nfa(automaton1, automaton2):
    pass


def expand_transitions(automaton, variables, mapping, old_num_vars):
    """
    Expands transitions in an automaton for a new set of variables.

    Args:
        automaton: The NFA object (e.g., mata_nfa.Nfa).
        variables: A list or tuple of new variable names/identifiers.
                   The length determines num_vars.
        mapping: A dictionary mapping new variable indices to old variable indices.
                 {new_var_idx: old_var_idx}. If old_var_idx is None, it's a new var.
                 More accurately, as per user code: template[new_idx] = old_label_tuple[old_idx]
                 So, mapping keys are indices in the *new* variable set,
                 and values are indices in the *old* variable set from which to take the bit.
        old_num_vars: The number of variables the automaton's labels originally corresponded to.
    """
    num_vars = len(variables)

    # --- Phase 1: Collect all original transition data ---
    # This avoids issues with modifying the automaton while iterating over its transitions.
    original_transitions_data = []
    # get_trans_as_sequence() should ideally return objects that allow access
    # to source, symbol, and target.
    # If it returns tuples (source, symbol, target), adapt accordingly.
    current_transitions_snapshot = list(automaton.get_trans_as_sequence())

    for t_info in current_transitions_snapshot:
        # Adapt access to source, symbol, target based on what get_trans_as_sequence() returns
        # If t_info is an object:
        if hasattr(t_info, 'source') and hasattr(t_info, 'symbol') and hasattr(t_info, 'target'):
            original_transitions_data.append({
                "source": t_info.source,
                "target": t_info.target,
                "symbol": t_info.symbol,  # This should be the integer representation
                "original_transition_ref": t_info  # Store the original reference for removal
            })
        # If t_info is a tuple (source, symbol, target):
        elif isinstance(t_info, tuple) and len(t_info) == 3:
            original_transitions_data.append({
                "source": t_info[0],
                "target": t_info[2],
                "symbol": t_info[1],  # This should be the integer representation
                "original_transition_ref": t_info  # Store the original tuple for removal
            })
        else:
            print(f"Warning: Encountered unknown transition format: {t_info}")
            continue

    # --- Phase 2: Remove all original transitions that will be expanded ---
    # It's crucial that remove_trans can correctly identify and remove the transition
    # based on original_transition_ref.
    for data in original_transitions_data:
        automaton.remove_trans(data["original_transition_ref"])

    # --- Phase 3: Calculate and add all new expanded transitions ---
    for data in original_transitions_data:
        source = data["source"]
        target = data["target"]
        old_label_int = data["symbol"]  # Integer symbol from the original transition

        # Convert the integer label to its bit tuple representation based on old_num_vars
        try:
            old_label_tuple = int_to_lsbf(old_label_int, old_num_vars)
        except ValueError as e:
            print(f"Error converting old_label {old_label_int} with {old_num_vars} bits: {e}")
            continue

        # Build a template for the new label tuple (length num_vars)
        # Initialize with None, then fill in bits from the old_label_tuple based on mapping.
        template = [None] * num_vars
        for new_idx, old_idx in mapping.items():
            if old_idx is not None:  # old_idx refers to an index in old_label_tuple
                if 0 <= old_idx < len(old_label_tuple):
                    template[new_idx] = old_label_tuple[old_idx]
                else:
                    # This indicates a potential mismatch between mapping, old_num_vars,
                    # and the structure of old_label_tuple.
                    print(
                        f"Warning: old_idx {old_idx} out of bounds for old_label_tuple (len {len(old_label_tuple)}) from old_label_int {old_label_int}.")
                    # Decide how to handle: skip, error, or treat as wildcard?
                    # For now, it will remain None and become a wildcard.
                    pass

                    # Identify positions in the template that are still None (these are new/unmapped variables)
        wildcard_indices = [i for i, val in enumerate(template) if val is None]

        # Generate all combinations of bits (0 or 1) for these wildcard positions
        num_wildcards = len(wildcard_indices)
        for bits_for_wildcards in itertools.product((0, 1), repeat=num_wildcards):
            new_label_list = list(template)  # Create a mutable copy of the template

            # Fill in the wildcard positions with the current combination of bits
            for i, bit_value in enumerate(bits_for_wildcards):
                wildcard_pos = wildcard_indices[i]
                new_label_list[wildcard_pos] = bit_value

            # At this point, new_label_list should be fully populated (no Nones)
            if None in new_label_list:
                print(f"Error: 'None' still present in new_label_list: {new_label_list}. "
                      f"Template: {template}, Wildcards: {wildcard_indices}, Bits: {bits_for_wildcards}")
                continue

            new_label_tuple = tuple(new_label_list)
            new_symbol_int = lsbf_to_int(new_label_tuple)

            automaton.add_transition(source, new_symbol_int, target)

    return automaton


def union(automaton1, automaton2, variables1, variables2):
    variables_merged = deepcopy(variables1)
    for var in variables2:
        if var not in variables1:
            variables_merged.append(var)
    setup(len(variables_merged))
    map1 = {}
    for i in range(len(variables1)):
        map1[i] = i
    map2 = {}
    for var in variables2:
        new_index = variables_merged.index(var)
        old_index = variables2.index(var)
        map2[new_index] = old_index
    automaton1 = expand_transitions(automaton1, variables_merged, map1, len(variables1))
    #print(f"automaton1 after expansion: {automaton1.to_dot_str()}")
    automaton2 = expand_transitions(automaton2, variables_merged, map2, len(variables2))
    #print(f"automaton2 after expansion: {automaton2.to_dot_str()}")
    return mata_nfa.union(automaton1, automaton2), variables_merged


def complete(automaton : mata_nfa.Nfa, variables):
    new_transitions = []
    states = automaton.get_reachable_states()
    for state in states:
        transitions = automaton.get_trans_from_state_as_sequence(state)
        needed_labels = set(range(2**len(variables)))
        for transition in transitions:
            needed_labels.discard(transition.symbol)
        for label in needed_labels:
            new_transitions.append((state, label))
    if not new_transitions:
        return automaton
    catch_state = automaton.add_state()
    for transition in new_transitions:
        source = transition[0]
        label = transition[1]
        automaton.add_transition(source, label, catch_state)
    return automaton


def complement(automaton : mata_nfa.Nfa):
    # This function will create a complement of the automaton
    # You will need to implement this based on your automata library
    new_final_states = set()
    #print(f"without negation: {automaton.to_dot_str()}")
    all_states = set(automaton.get_reachable_states())
    #print(f"All states: {all_states}")
    #print(f"final states: {automaton.final_states}")
    for state in all_states:
        #print(f"State: {state}")
        if state not in automaton.final_states:
            #print(f"State {state} is not in final states")
            new_final_states.add(state)
    automaton.final_states = new_final_states
    #print(f"Final states: {new_final_states}")
    return automaton

def determinize(automaton : mata_nfa.Nfa):
    # This function will discretize the automaton
    # You will need to implement this based on your automata library
    return mata_nfa.determinize(automaton)

def count_tree(node):
    coefficients = {}
    ones = 0
    def helper(t, i):
        nonlocal ones
        if isinstance(t, Var):
            coefficients[t.name] = coefficients.get(t.name, 0) + i
        elif isinstance(t, One):
            ones -= i                      # already there
        elif isinstance(t, Const):         # NEW  (handles ±N)
            ones -= i * t.value
        elif isinstance(t, Zero):
            pass
        elif isinstance(t, Add):
            helper(t.left,  i)
            helper(t.right, i)
        elif isinstance(t, Sub):
            helper(t.left,  i)
            helper(t.right, -i)
        else:
            raise ValueError(f"Unexpected term node: {type(t)}")
    helper(node.left, 1)
    helper(node.right, -1)
    return ones, coefficients


def is_deterministic(aut : mata_nfa.Nfa):
    # This function will check if the automaton is deterministic
    # You will need to implement this based on your automata library
    return aut.is_deterministic()


def lsbf_to_int(bits):
    return sum(bit << i for i, bit in enumerate(bits))

def encode(k):
    if k < 0:
        return -2*k + 1
    else:
        return 2*k

def decode(k):
    if k % 2 == 0:
        return k // 2
    else:
        return (k-1) // -2