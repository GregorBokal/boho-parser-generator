from boho.objects import Tree, Token
from boho.interpreter import Interpreter


class ArithmeticInterpreter(Interpreter):

    def start(self, tree: Tree):
        return self(tree[0])

    def sum(self, tree: Tree):
        return sum([self(c) for c in tree])

    def prod(self, tree: Tree):
        a = int(self(tree[0]))
        if len(tree) > 1:
            return a * int(self(tree[1]))
        else:
            return a


def make_prod(a, b=None):
    children = [Token('INT', str(a))]
    prod_node = Tree('prod', children)
    if b is not None:
        return Tree('prod', [prod_node, Token('INT', str(b))])
    return prod_node


def make_sum(*prods):
    if len(prods) == 1:
        return Tree('sum', [prods[0]])
    # Left-recursive: sum -> sum + prod
    return Tree('sum', [make_sum(*prods[:-1]), prods[-1]])


def make_tree(sum_node):
    return Tree('start', [sum_node])


class TestInterpreterBaseClass:

    def test_token_without_handler_returns_value(self):
        interp = Interpreter()
        tok = Token('NUMBER', '42')
        assert interp(tok) == '42'

    def test_tree_without_handler_returns_list(self):
        interp = Interpreter()
        tree = Tree('unknown', [Token('A', 'x'), Token('B', 'y')])
        assert interp(tree) == ['x', 'y']

    def test_nested_tree_without_handler(self):
        interp = Interpreter()
        tree = Tree('outer', [
            Tree('inner', [Token('X', '1'), Token('Y', '2')]),
            Token('Z', '3')
        ])
        assert interp(tree) == [['1', '2'], '3']

    def test_tree_with_handler(self):
        class Custom(Interpreter):
            def my_node(self, tree: Tree):
                return 'handled'

        interp = Custom()
        tree = Tree('my_node', [Token('A', 'x')])
        assert interp(tree) == 'handled'

    def test_token_with_handler(self):
        class Custom(Interpreter):
            def NUM(self, token: Token):
                return int(token.value)

        interp = Custom()
        assert interp(Token('NUM', '7')) == 7

    def test_empty_tree_without_handler(self):
        interp = Interpreter()
        tree = Tree('empty', [])
        assert interp(tree) == []


class TestArithmeticInterpreter:

    def test_single_number(self):
        # 5
        interp = ArithmeticInterpreter()
        tree = make_tree(make_sum(make_prod(5)))
        assert interp(tree) == 5

    def test_simple_addition(self):
        # 3 + 4 = 7
        interp = ArithmeticInterpreter()
        tree = make_tree(make_sum(make_prod(3), make_prod(4)))
        assert interp(tree) == 7

    def test_simple_multiplication(self):
        # 2 * 3 = 6
        interp = ArithmeticInterpreter()
        tree = make_tree(make_sum(make_prod(2, 3)))
        assert interp(tree) == 6

    def test_mixed_expression(self):
        # 1 + 2 * 3 = 7
        interp = ArithmeticInterpreter()
        tree = make_tree(make_sum(make_prod(1), make_prod(2, 3)))
        assert interp(tree) == 7

    def test_multiple_additions(self):
        # 1 + 2 + 3 = 6
        interp = ArithmeticInterpreter()
        tree = make_tree(make_sum(make_prod(1), make_prod(2), make_prod(3)))
        assert interp(tree) == 6

    def test_zero(self):
        # 0
        interp = ArithmeticInterpreter()
        tree = make_tree(make_sum(make_prod(0)))
        assert interp(tree) == 0

    def test_multiply_by_one(self):
        # 1 * 7 = 7
        interp = ArithmeticInterpreter()
        tree = make_tree(make_sum(make_prod(1, 7)))
        assert interp(tree) == 7

    def test_example_from_docs(self):
        # 1 + 2 * 3 = 7 (the exact tree from examples/interpreter_example.py)
        interp = ArithmeticInterpreter()
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
        assert interp(t) == 7
