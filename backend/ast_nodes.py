# ast_nodes.py

# Term classes
class Var:
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return self.name

class Zero:
    def __repr__(self):
        return "0"

class One:
    def __repr__(self):
        return "1"

class Const:
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return str(self.value)

class Add:
    def __init__(self, left, right):
        self.left = left
        self.right = right
    def __repr__(self):
        return f"({self.left} + {self.right})"

class Sub:
    def __init__(self, left, right):
        self.left = left
        self.right = right
    def __repr__(self):
        return f"({self.left} - {self.right})"

class Mult:
    def __init__(self, n, var):
        self.n = n
        self.var = var
    def __repr__(self):
        return f"{self.n}{self.var}"

# Formula classes
class LessEqual:
    def __init__(self, left, right):
        self.left = left
        self.right = right
    def __repr__(self):
        return f"({self.left} <= {self.right})"

class Eq:
    def __init__(self, left, right):
        self.left = left
        self.right = right
    def __repr__(self):
        return f"({self.left} = {self.right})"

class Less:
    def __init__(self, left, right):
        self.left = left
        self.right = right
    def __repr__(self):
        return f"({self.left} < {self.right})"

class Greater:
    def __init__(self, left, right):
        self.left = left
        self.right = right
    def __repr__(self):
        return f"({self.left} > {self.right})"

class GreaterEqual:
    def __init__(self, left, right):
        self.left = left
        self.right = right
    def __repr__(self):
        return f"({self.left} >= {self.right})"

class Exists:
    def __init__(self, var, formula):
        self.var = var
        self.formula = formula
    def __repr__(self):
        return f"Exists({self.var}, {self.formula})"

class Or:
    def __init__(self, left, right):
        self.left = left
        self.right = right
    def __repr__(self):
        return f"({self.left} OR {self.right})"

class And:
    def __init__(self, left, right):
        self.left = left
        self.right = right
    def __repr__(self):
        return f"({self.left} AND {self.right})"

class Not:
    def __init__(self, expr):
        self.expr = expr
    def __repr__(self):
        return f"(NOT {self.expr})"

class Implies:
    def __init__(self, left, right):
        self.left = left
        self.right = right
    def __repr__(self):
        return f"({self.left} -> {self.right})"

class Iff:
    def __init__(self, left, right):
        self.left = left
        self.right = right
    def __repr__(self):
        return f"({self.left} <-> {self.right})"

class ForAll:
    def __init__(self, var, formula):
        self.var = var
        self.formula = formula
    def __repr__(self):
        return f"ForAll({self.var}, {self.formula})"