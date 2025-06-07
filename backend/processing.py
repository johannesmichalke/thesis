import os
import re
from collections import defaultdict
from typing import List, Tuple

from lark import UnexpectedInput

import syntax_tree_visualizier  # type: ignore
import parser  # type: ignore
import expander  # type: ignore
from automaton_builder import build_automaton, is_deterministic, determinize  # type: ignore
import libmata.nfa.nfa as mata_nfa  # type: ignore

from solutions import find_shortest_paths, describe_paths


###############################################################################
# Helper utilities                                                             #
###############################################################################


def int_to_bitstring(i: int, width: int) -> str:
    """
    Return *width*-bit two’s-complement binary representation of *i*
    *little-endian* (LSB-first) so it matches the automaton’s encoding.
    """
    return f"{i:0{width}b}"[::-1]          # <— reverse to LSB-first


###############################################################################
# Wild-card compression utilities                                              #
###############################################################################


def _can_merge(a: str, b: str) -> str | None:
    """Return merged pattern if *a* and *b* differ by **exactly one** concrete bit.

    Both patterns must have equal length. The merge is only permitted when the
    differing position contains concrete bits (``0``/``1``) in both patterns
    (never ``*``). The result is the pattern with a ``*`` at that position.
    Otherwise ``None`` is returned.
    """
    if len(a) != len(b):
        return None

    diff_pos = -1
    for idx, (ca, cb) in enumerate(zip(a, b)):
        if ca == cb:
            continue
        # Abort if either side already has a wildcard here.
        if ca == "*" or cb == "*":
            return None
        # More than one differing bit? no merge.
        if diff_pos != -1:
            return None
        diff_pos = idx

    if diff_pos == -1:  # identical
        return None

    merged = list(a)
    merged[diff_pos] = "*"
    return "".join(merged)


def _compress_bit_patterns(patterns: List[str]) -> List[str]:
    """Iteratively merge patterns using the * wildcard.

    The algorithm keeps merging two patterns whenever they can be merged until
    no more merges are possible. The resulting list is returned *sorted* for
    determinism.
    """
    work: set[str] = set(patterns)

    merged_something = True
    while merged_something:
        merged_something = False
        items = list(work)
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                merged = _can_merge(items[i], items[j])
                if merged:
                    work.discard(items[i])
                    work.discard(items[j])
                    work.add(merged)
                    merged_something = True
                    break
            if merged_something:
                break

    return sorted(work)


def compress_label_string(label_str: str) -> str:
    """Compress a comma-separated list of bit-strings using wild-cards.

    Example::
        >>> compress_label_string("01,10,11")
        '01,1*'
    """
    labels = [lbl.strip() for lbl in label_str.split(",") if lbl.strip()]
    if not labels:
        return ""
    compressed = _compress_bit_patterns(labels)
    return ",".join(compressed)


###############################################################################
# DOT helper: reorder bit-labels after a variable permutation                  #
###############################################################################

def _reorder_bit_patterns_in_label(label: str,
                                   mapping: dict[int, int],
                                   width: int) -> str:
    """
    Reorder every bit-pattern inside *label* according to *mapping*.

    *label* is the raw string that appears inside `label="..."` – it can contain
    several comma-separated patterns that may include wild-cards (`*`).

    Any pattern that
        * has length *width*, **and**
        * consists only of `0 1 *`
    is permuted; everything else (epsilon, 'ε', etc.) is left unchanged.
    """
    parts = [p.strip() for p in label.split(",") if p.strip()]
    new_parts: list[str] = []

    inv = {new_idx: old_idx for old_idx, new_idx in mapping.items()}

    for p in parts:
        if len(p) == width and all(c in "01*" for c in p):
            reordered = [""] * width
            for new_idx in range(width):
                old_idx = inv[new_idx]
                reordered[new_idx] = p[old_idx]
            new_parts.append("".join(reordered))
        else:
            new_parts.append(p)            # untouched (epsilon, etc.)

    return ",".join(new_parts)


def reorder_bitstring_labels(dot: str,
                             mapping: dict[int, int],
                             width: int) -> str:
    """
    Apply the bit-position permutation encoded in *mapping* to **all** edge
    labels in *dot* and return the updated DOT string.
    """
    label_re = re.compile(r'(\[label=")([^"]*)("\])')

    def _repl(m: re.Match[str]) -> str:
        prefix, raw, suffix = m.groups()
        new_raw = _reorder_bit_patterns_in_label(raw, mapping, width)
        return f'{prefix}{new_raw}{suffix}'

    return label_re.sub(_repl, dot)


###############################################################################
# DOT manipulation                                                             #
###############################################################################

# Matches lines of the form "  2 -> { 3 } [label=\"0,1\"] ;"
_EDGE_LINE = re.compile(r"^(\s*)(\d+)\s*->\s*\{\s*(\d+)\s*\}\s*\[(.*)\];\s*$")
_LABEL_ATTR = re.compile(r'label\s*=\s*"([^"]*)"')


def convert_int_labels_to_bitstrings(dot: str, width: int) -> str:
    """Replace integer edge labels with binary strings of *width* bits."""

    def _repl(match: re.Match[str]) -> str:
        raw = match.group(1)
        parts = [p.strip() for p in raw.split(",")]
        converted: list[str] = []
        for part in parts:
            if part.isdigit():
                converted.append(int_to_bitstring(int(part), width))
            else:  # already something else (epsilon, *, ...)
                converted.append(part)
        return f'label="{",".join(converted)}"'

    return _LABEL_ATTR.sub(_repl, dot)


###############################################################################
# New step 1: merge parallel edges                                             #
###############################################################################


def merge_parallel_edges(dot: str) -> str:
    """Combine parallel edges (same *src* ➜ *dst*) and concatenate their labels.

    The labels are **not** compressed here – we simply unify them into a single
    comma-separated list. Wild-card compression is handled in a later pass.
    """
    groups: dict[Tuple[str, str, str], List[str]] = defaultdict(list)
    header: List[str] = []
    footer: List[str] = []
    in_edges = False

    for line in dot.splitlines(keepends=True):
        m = _EDGE_LINE.match(line)
        if m:
            in_edges = True
            indent, src, dst, attrs = m.groups()
            lab_match = _LABEL_ATTR.search(attrs)
            if lab_match:
                labels = [l.strip() for l in lab_match.group(1).split(",") if l.strip()]
            else:
                labels = []
            groups[(indent, src, dst)].extend(labels)
        else:
            # Decide whether we are before or after the edge section.
            (header if not in_edges else footer).append(line)

    merged_edge_lines: List[str] = []
    for (indent, src, dst), labels in groups.items():
        # Keep original order but remove duplicates.
        seen: set[str] = set()
        uniq_labels = []
        for lbl in labels:
            if lbl not in seen:
                seen.add(lbl)
                uniq_labels.append(lbl)
        label_str = ",".join(uniq_labels)
        merged_edge_lines.append(
            f"{indent}{src} -> {{ {dst} }} [label=\"{label_str}\"]\n"
        )

    return "".join(header) + "".join(merged_edge_lines) + "".join(footer)


###############################################################################
# New step 2: apply wild-card compression to each edge label                  #
###############################################################################


def _merge_patterns(patterns):
    """
    Repeatedly merge sub-labels that differ in exactly one position,
    replacing that position with ‘*’, until no further merges are possible.
    """
    patterns = set(patterns)
    changed = True

    while changed:
        changed = False
        new_patterns, merged = set(), set()
        pat_list = list(patterns)

        for i in range(len(pat_list)):
            for j in range(i + 1, len(pat_list)):
                a, b = pat_list[i], pat_list[j]
                if len(a) != len(b):
                    continue

                # Compare character-wise
                diff, combo = 0, []
                for c1, c2 in zip(a, b):
                    if c1 == c2:
                        combo.append(c1)
                    else:
                        diff += 1
                        combo.append('*')
                    if diff > 1:
                        break

                # Merge if they differed in **exactly** one place
                if diff == 1:
                    merged.update({a, b})
                    new_patterns.add(''.join(combo))

        # Anything not merged stays; add all new combos
        next_round = (patterns - merged) | new_patterns
        if next_round != patterns:
            patterns, changed = next_round, True

    return patterns


def simplify_automaton_labels(dot: str) -> str:
    """
    Take a DOT string of a finite automaton, merge the transition
    labels per the given rule, and return the updated DOT string.
    """
    label_re = re.compile(r'\[label="([^"]+)"\]')

    def _replace(match):
        raw = match.group(1)
        parts = [p.strip() for p in raw.split(',')]
        merged = _merge_patterns(parts)
        return f'[label="{", ".join(sorted(merged))}"]'

    return label_re.sub(_replace, dot)

###############################################################################

def add_rankdir_auto(dot: str) -> str:
    """
    Inspects the bounding box and node count in the DOT string and inserts:
    - rankdir=LR or TB depending on shape
    - ratio=fill only if node count exceeds a threshold
    """
    lines = dot.strip().splitlines()

    # 1. Try to extract bounding box
    width = height = None
    for line in lines:
        if 'bb="' in line:
            match = re.search(r'bb="0,0,(\d+),(\d+)"', line)
            if match:
                width = int(match.group(1))
                height = int(match.group(2))
            break

    # 2. Count nodes
    node_lines = [line for line in lines if re.match(r'^\s*\d+\s+\[', line)]
    node_count = len(node_lines)

    # 3. Decide layout direction
    rankdir = "LR" if width and height and width > height else "TB"

    # 4. Insert layout instructions
    for i, line in enumerate(lines):
        if line.strip().startswith("digraph"):
            # Insert after "digraph G {"
            insert_lines = [
                f'layout=dot;',
                f'rankdir={rankdir};',
                'size="12,8";'
            ]
            if node_count >= 5:  # apply ratio=fill only if graph is "big enough"
                insert_lines.insert(0, 'ratio=fill;')
            for j, content in enumerate(insert_lines):
                lines.insert(i + 1 + j, content)
            break

    return "\n".join(lines)
###############################################################################
# Pipeline                                                                     #
###############################################################################


def formula_to_dot(formula: str, variable_order, k_solutions):
    tree = parser.parse_formula(formula)  # may raise UnexpectedInput
    pure_tree = expander.expand_shorthands(tree)
    syntax_tree_visualizier.syntax_tree_to_dot(tree, filename="syntax_tree")

    aut, variables = build_automaton(pure_tree)
    if not is_deterministic(aut):
        aut = determinize(aut)
    aut = mata_nfa.minimize(aut)
    example_solutions = find_shortest_paths(aut, k_solutions)
    dot = aut.to_dot_str()
    dot = convert_int_labels_to_bitstrings(dot, len(variables))
    if variable_order:
        example_solutions = describe_paths(variables, example_solutions, variable_order)
        if set(variable_order) != set(variables):
            raise AssertionError(
                "variable_order must be a permutation of the internal "
                f"variables {variables}, got {variable_order}"
            )
        mapping = {
            old_idx: variable_order.index(var)
            for old_idx, var in enumerate(variables)
        }
        dot = reorder_bitstring_labels(dot, mapping, len(variables))
        variables = variable_order[:]
    else:
        example_solutions = describe_paths(variables, example_solutions)
    dot = merge_parallel_edges(dot)
    dot = simplify_automaton_labels(dot)
    dot = add_rankdir_auto(dot)
    return variables, dot, example_solutions


###############################################################################
# CLI / demo                                                                   #
###############################################################################


def main() -> None:
    example = "(EX z. x = 4z) AND (EX w. y = 4w)"  # sample input
    vars_, dot_out = formula_to_dot(example)

    # Write DOT file next to script for inspection.
    out_path = os.path.join(os.path.dirname(__file__), "graph.dot")
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(dot_out)
    print(f"Wrote DOT ({len(vars_)} variables) to {out_path}")


if __name__ == "__main__":
    main()
