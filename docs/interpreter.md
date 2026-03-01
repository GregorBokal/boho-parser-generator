# Interpreter

---

## Description

The interpreter is used for "walking" the syntax tree
and executing desired actions. A generic `Interpreter`
class is provided, which can then be used as a base
for building an interpreter for a specific language.

## Generic class

The class on which concrete interpreters are based is the following:

```python
class Interpreter:
    def __call__(self, node: Tree | Token):
        # If we implement a function with the same name as the node name,
        if hasattr(self, node.name):
            # use it.
            return getattr(self, node.name)(node)
        # If no such function exists and the node is a token,
        elif isinstance(node, Token):
            # the interpreter returns the token's value.
            return node.value
        # If it is a subtree (nonterminal),
        else:
            # return a list of processed child nodes.
            return [self(p) for p in node.children]
```

## Usage example

```python
from boho.interpreter import Interpreter
from boho.objects import Tree, Token


class MyInterpreter(Interpreter):

    def start(self, tree: Tree):
        print(self(tree[0]))

    def expression(self, tree: Tree):
        return sum([self(c) for c in tree])

    def term(self, tree: Tree):
        a = int(self(tree[0]))
        if len(tree) > 1:
            return a * int(self(tree[1]))
        else:
            return a


# Syntax tree for the expression 1 + 2 * 3
# in the form produced by the parser:
t = Tree('start', [
    Tree('expression', [
        Tree('expression', [
            Tree('term', [
                Token('INT', '1')
            ])
        ]),
        Tree('term', [
            Tree('term', [
                Token('INT', '2')
            ]),
            Token('INT', '3')
        ])
    ])
])

interpreter = MyInterpreter()
print(t.pretty())
interpreter(t)
```
