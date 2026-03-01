from boho.objects import Tree, Token
from boho.interpreter import Interpreter


class MyInterpreter(Interpreter):

    def start(self, tree: Tree):
        print(self(tree[0]))

    def sum(self, tree: Tree):
        return sum([self(c) for c in tree])

    def prod(self, tree: Tree):
        a = int(self(tree[0]))
        if len(tree) > 1:
            return a * int(self(tree[1]))
        else:
            return a


# 1 + 2 * 3
t = Tree('start', [
    Tree('sum', [
        Tree('sum', [
            Tree('prod', [
                Token('INT', '1')
            ])
        ]),
        Tree('prod', [
            Tree('prod', [
                Token('INT', '2')
            ]),
            Token('INT', '3')
        ])
    ])
])

interpreter = MyInterpreter()
print(t.pretty())
interpreter(t)
