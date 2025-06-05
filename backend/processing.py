import os
import subprocess
import tempfile

from lark import UnexpectedInput

import syntax_tree_visualizier
import parser
import re
import expander
from automaton_builder import build_automaton, setup
from libmata.alphabets import *
from automaton_builder import is_deterministic
from automaton_builder import determinize
import libmata.nfa.nfa as mata_nfa
from collections import defaultdict



def run_or_fail(cmd, **kwargs):
    """Run a command and raise an exception with full stdout/stderr if it fails."""
    from subprocess import run, PIPE

    result = run(cmd, stdout=PIPE, stderr=PIPE, text=True, **kwargs)
    if result.returncode != 0:
        raise RuntimeError(
            f"\n\n🚨 Command failed: {' '.join(cmd)}\n\n"
            f"--- STDOUT ---\n{result.stdout}\n"
            f"--- STDERR ---\n{result.stderr}"
        )
    return result.stdout


def parse_graphviz_to_json(dot_str: str):
    nodes = {}
    edges = []
    initial = None

    lines = dot_str.strip().splitlines()

    for line in lines:
        line = line.strip()

        # Match accepting states (doublecircle)
        m_accepting = re.match(r'(\w+)\s+\[shape=doublecircle\];', line)
        if m_accepting:
            state = m_accepting.group(1)
            nodes[state] = {"id": f"q{state}", "accepting": True}
            continue

        # Match initial state (i0 -> ...)
        m_initial = re.match(r'i0\s+->\s+(\w+);', line)
        if m_initial:
            initial = f"q{m_initial.group(1)}"
            continue

        # Match edges with LaTeX labels
        m_edge = re.match(r'(\w+)\s+->\s+\{\s*(\w+)\s*\}\s+\[.*texlbl="(.*?)"\];', line)
        if m_edge:
            src, tgt, texlbl = m_edge.groups()
            src_id = f"q{src}"
            tgt_id = f"q{tgt}"
            labels = [label.strip() for label in texlbl.split(r",\,")]
            edges.append({
                "source": src_id,
                "target": tgt_id,
                "labels": labels
            })
            # Ensure nodes are present
            for s in [src, tgt]:
                if s not in nodes:
                    nodes[s] = {"id": f"q{s}", "accepting": False}

    return {
        "nodes": list(nodes.values()),
        "edges": edges,
        "initial": initial
    }

_edge_line = re.compile(r'^(\s*)(\d+)\s*->\s*\{\s*(\d+)\s*\}\s*\[(.*)\];\s*$')

def combine_parallel_edges(dot: str) -> str:
    groups = defaultdict(list)
    header = []
    footer = []
    in_edges = False

    # We’ll collect the “other” lines into header until we hit the first edge,
    # then into footer once we’ve passed all edges.
    for line in dot.splitlines(keepends=True):
        m = _edge_line.match(line)
        if m:
            in_edges = True
            indent, src, dst, attrs = m.groups()
            # find the texlbl="…"
            tm = re.search(r'texlbl="([^"]+)"', attrs)
            if tm:
                raw = tm.group(1).strip().strip('$')
                groups[(indent, src, dst)].append(raw)
            else:
                # if it has no texlbl, treat it as footer (or you could pass it through)
                footer.append(line)
        else:
            if not in_edges:
                header.append(line)
            else:
                footer.append(line)

    # build merged edges
    merged = []
    for (indent, src, dst), raws in groups.items():
        # join with commas (and a little spacing)
        combo = ',\\,'.join(raws)
        tex = f'${combo}$'
        merged.append(
            f'{indent}{src} -> {{ {dst} }} [label=" " texlbl="{tex}"];\n'
        )

    return ''.join(header) + ''.join(merged) + ''.join(footer)


def bit_vector_latex_map(n):
    """
    Returns a dict mapping each raw LaTeX vector (as a Python str)
    to its integer index.
    """
    result = {}
    for i in range(2 ** n):
        bits = f"{i:0{n}b}"
        # join bits with LaTeX linebreaks "\\" to get, e.g., "0\\1"
        body = r"\\".join(bits)
        tex = r"\left[\begin{array}{c}" + body + r"\end{array}\right]"
        result[tex] = i
    return result

def replace_dot_labels_with_latex(dot_str: str, n: int) -> str:
    raw_map = {v: k for k, v in bit_vector_latex_map(n).items()}

    latex_map = {}
    for i, raw in raw_map.items():
        latex_map[i] = raw  # don't add $ here

    def _repl(m):
        raw_vals = m.group(1).split(',')
        texlbls = []

        for val in raw_vals:
            val = val.strip()
            if '\\begin{array}' in val:  # already LaTeX
                texlbls.append(val)
            else:
                try:
                    idx = int(val)
                    tex = latex_map.get(idx, val)
                except ValueError:
                    tex = val
                texlbls.append(tex)

        joined = ',\\,'.join(texlbls)
        return f'label=" " texlbl="$' + joined + '$"'

    return re.sub(r'label="([^"]+)"', _repl, dot_str)
#∃z(x= 4z) ∧∃w(y= 4w)


def prettify_dot(dot_str: str) -> str:
    header = r"""
rankdir=LR;
splines=true;
overlap=false;
nodesep=0.6;
ranksep=0.7;
margin=0.15;
graph  [dpi=110];
node   [shape=circle, fixedsize=true, width=0.6, height=0.6,
        fontname="Latin Modern Math", fontsize=11];
edge   [fontname="Latin Modern Math", fontsize=10, labelfloat=false];
"""
    return dot_str.replace("digraph finiteAutomaton {",
                           "digraph finiteAutomaton {\n" + header,
                           1)


def string_to_automaton(string):
     #  OR
    try:
        tree = parser.parse_formula(string)  # Invalid formula
    except UnexpectedInput as e:
        raise e
    pure_tree = expander.expand_shorthands(tree)
    syntax_tree_visualizier.syntax_tree_to_dot(tree, filename="syntax_tree")
    aut, variables = build_automaton(pure_tree)
    if not is_deterministic(aut):
        aut = determinize(aut)
    aut = mata_nfa.minimize(aut)
    dot_string = aut.to_dot_str()
    print(dot_string)
    dot_string = combine_parallel_edges(dot_string)
    print(dot_string)
    dot_string = replace_dot_labels_with_latex(dot_string, len(variables))
    print(dot_string)
    dot_string = prettify_dot(dot_string)
    #payload = parse_graphviz_to_json(dot_string)
    #print("step1 done")
    with tempfile.TemporaryDirectory() as tmp:
        # --- filenames INSIDE tmp ---
        dot_file = "graph.dot"
        tikz_raw = "graph_raw.tex"
        tex_file = "graph.tex"
        pdf_file = "graph.pdf"
        svg_file = "graph.svg"

        # 1. write DOT
        with open(os.path.join(tmp, dot_file), "w") as f:
            f.write(dot_string)

        # 2. dot2tex
        run_or_fail(
            ["dot2tex",
             "--figonly",
             "-ftikz",
             "--tikzedgelabels",
             "--autosize",  # shrink to content
             "--graphstyle={>=latex}",
             dot_file,
             "-o", tikz_raw],
            cwd=tmp
        )

        # 3. wrap + write graph.tex
        with open(os.path.join(tmp, tikz_raw)) as f:
            tikz_code = f.read()
        wrapper = r"""\documentclass[tikz,border=0pt]{standalone}
        \usepackage{amsmath}
        \usepackage{tikz}
        \tikzset{
          every edge node/.style={sloped, font=\small, midway}
        }
        \begin{document}
        """ + tikz_code + r"\end{document}"
        with open(os.path.join(tmp, tex_file), "w") as f:
            f.write(wrapper)

        # 4. pdflatex  (run IN tmp, no -output-directory flag needed)
        run_or_fail(
            ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex_file],
            cwd=tmp
        )

        # sanity-check
        full_pdf = os.path.join(tmp, pdf_file)
        if not os.path.isfile(full_pdf) or os.path.getsize(full_pdf) == 0:
            raise RuntimeError("graph.pdf missing or empty after pdflatex")

        with open(os.path.join(tmp, "graph.pdf"), "rb") as f:
            return variables, f.read()
        # 5. dvisvgm  (also IN tmp)
        #run_or_fail(
        #    ["dvisvgm", "--pdf", "--no-fonts", "--exact", "-p", "1",
        #     pdf_file, "-o", svg_file],
        #    cwd=tmp
        #)

        # 6. read SVG
        #with open(os.path.join(tmp, svg_file)) as f:
        #    svg_data = f.read()
    #return svg_data
    #dot_string = dot_string.replace(
    #    "digraph finiteAutomaton {",
    #    'digraph finiteAutomaton {\nrankdir=LR;\n splines=true;\n overlap=false;\n nodesep=0.5;\n ranksep=0.5;\n node [shape=circle width=0.6 fixedsize=true];\n edge [labelfloat=false];',
    #    1
    #)
    # Save DOT string to file
    #print(dot_string)
    #with open("graph.dot", "w") as f:
    #    f.write(dot_string)

    # Convert DOT to LaTeX (TikZ) with dot2tex
    #import subprocess
    #subpr
     # ocess.run(["dot2tex", "-tmath","graph.dot", "-o", "graph.tex"])

