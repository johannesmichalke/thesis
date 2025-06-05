# expander.py

from ast_nodes import *

def expand_shorthands(node):
    if isinstance(node, Zero):
        return Zero()

    if isinstance(node, One):
        return One()

    if isinstance(node, Var):
        return Var(node.name)

    if isinstance(node, Const):
        if node.value == 0:
            return Zero()

        if node.value > 0:  # positive constants stay as before
            result = One()
            for _ in range(node.value - 1):
                result = Add(result, One())
            return result

        # --- NEW: negative constants ---
        # −n  is rewritten as 0 −  n
        return Sub(Zero(), expand_shorthands(Const(-node.value)))

    if isinstance(node, Mult):
        result = Var(node.var)
        for _ in range(node.n - 1):
            result = Add(result, Var(node.var))
        return result

    if isinstance(node, Add):
        return Add(
            expand_shorthands(node.left),
            expand_shorthands(node.right)
        )

    if isinstance(node, Sub):  # NEW
        left = expand_shorthands(node.left)  # NEW
        right = expand_shorthands(node.right)  # NEW
        return Sub(left, right)  # NEW

    if isinstance(node, Const):  # NEW
        return node

    if isinstance(node, LessEqual):
        return LessEqual(
            expand_shorthands(node.left),
            expand_shorthands(node.right)
        )

    if isinstance(node, Eq):
        left = expand_shorthands(node.left)
        right = expand_shorthands(node.right)
        return expand_shorthands(And(LessEqual(left, right), LessEqual(right, left)))

    if isinstance(node, Less):
        left = expand_shorthands(node.left)
        right = expand_shorthands(node.right)
        return expand_shorthands(And(
            LessEqual(left, right),
            Not(And(LessEqual(left, right), LessEqual(right, left)))
        ))

    if isinstance(node, Greater):
        left = expand_shorthands(node.left)
        right = expand_shorthands(node.right)
        return expand_shorthands(Less(right, left))

    if isinstance(node, GreaterEqual):
        left = expand_shorthands(node.left)
        right = expand_shorthands(node.right)
        return LessEqual(
            expand_shorthands(right),
            expand_shorthands(left)
        )

    if isinstance(node, Implies):
        # a -> b becomes (NOT a) OR b
        left = expand_shorthands(node.left)
        right = expand_shorthands(node.right)
        return Or(Not(left), right)

    if isinstance(node, Iff):
        # a <-> b becomes (a -> b) AND (b -> a)
        left = expand_shorthands(node.left)
        right = expand_shorthands(node.right)
        return expand_shorthands(And(
            expand_shorthands(Implies(left, right)),
            expand_shorthands(Implies(right, left))
        ))
    if isinstance(node, ForAll):
        # ForAll(x, φ) becomes NOT(EXISTS x. NOT φ)
        return Not(Exists(
            node.var,
            expand_shorthands(Not(node.formula))
        ))

    if isinstance(node, Not):
        return Not(expand_shorthands(node.expr))

    if isinstance(node, Or):
        return Or(
            expand_shorthands(node.left),
            expand_shorthands(node.right)
        )

    if isinstance(node, And):
        # a AND b becomes NOT(NOT a OR NOT b)
        left = expand_shorthands(node.left)
        right = expand_shorthands(node.right)
        return Not(Or(Not(left), Not(right)))

    if isinstance(node, Exists):
        return Exists(node.var, expand_shorthands(node.formula))

    raise ValueError(f"Unknown node type: {type(node)}")