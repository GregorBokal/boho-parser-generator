import pytest

from boho.boho import Boho
from boho.grammar_interpreter import interpret
from boho.objects import Tree, Token


# ── Boho end-to-end ──────────────────────────────────────


class TestBohoEndToEnd:

    def test_simple_grammar(self):
        b = Boho('start: A\nA: "a"')
        tree = b('a')
        assert isinstance(tree, Tree)
        assert tree.name == 'start'

    def test_arithmetic_grammar(self):
        b = Boho('''
start: sum
sum: sum "+" product | product
product: product "*" atom | atom
atom: NUMBER
NUMBER: @INT
%ignore " "
        ''')
        tree = b('1 + 2 * 3')
        assert tree.name == 'start'

    def test_ignored_whitespace_multi_char(self):
        """Multi-character ignored literal (non-single-char) goes
        through the parser's ignore rather than the lexer's."""
        b = Boho('''
start: A+
A: "a"
%ignore "::"
        ''')
        tree = b('a::a::a')
        assert tree.name == 'start'

    def test_nonterminal_with_alias(self):
        """The `-> alias` annotation should create a named option."""
        b = Boho('''
start: line
line: A -> named
A: "a"
        ''')
        tree = b('a')
        # the named alternative produces a subtree called `named`
        assert any(isinstance(c, Tree) and c.name == 'named'
                   for c in walk(tree))

    def test_optional_quantifier(self):
        b = Boho('''
start: A B?
A: "a"
B: "b"
        ''')
        assert b('a').name == 'start'
        assert b('ab').name == 'start'

    def test_star_quantifier(self):
        b = Boho('''
start: A*
A: "a"
        ''')
        assert b('').name == 'start'
        assert b('aaa').name == 'start'

    def test_plus_quantifier(self):
        b = Boho('''
start: A+
A: "a"
        ''')
        assert b('a').name == 'start'
        assert b('aaa').name == 'start'

    def test_parentheses_grouping(self):
        b = Boho('''
start: (A B)+
A: "a"
B: "b"
        ''')
        tree = b('ababab')
        assert tree.name == 'start'

    def test_mode_push_and_pop(self):
        """Grammar referencing tokens from multiple lexer modes."""
        b = Boho('''
start: WORD LPAREN INT RPAREN WORD
WORD: /[a-z]+/
LPAREN: "(" -> +e

#e
INT: @INT
RPAREN: ")" -> -
        ''')
        tree = b('foo(1)baz')
        assert tree.name == 'start'

    def test_mode_reset(self):
        """A pop count of 2 empties a two-level stack."""
        b = Boho('''
start: A OPEN INNER CLOSE

A: "a"
OPEN: "(" -> +sub

#sub
CLOSE: ")" -> -2
INNER: "x"
        ''')
        tree = b('a(x)')
        assert tree.name == 'start'

    def test_mode_change_in_place(self):
        b = Boho('''
start: _body+
_body: A | B
A: "a" -> second

#second
B: "b"
        ''')
        tree = b('ab')
        assert tree.name == 'start'

    def test_fake_terminal(self):
        """A fake terminal (UPPER_ ending with underscore) is defined
        like a nonterminal but collapses into a single Token."""
        b = Boho('''
start: NUM_
NUM_: DIGIT DIGIT
DIGIT: /\\d/
        ''')
        tree = b('42')
        # NUM_ should collapse into one token carrying '42'
        assert len(tree) == 1
        tok = tree[0]
        assert isinstance(tok, Token)
        assert tok.name == 'NUM_'
        assert tok.value == '42'

    def test_regex_terminal(self):
        b = Boho('''
start: ID
ID: /[a-z][a-z0-9]*/
        ''')
        assert b('abc123').name == 'start'


# ── interpret() entry point ──────────────────────────────


class TestInterpretFunction:

    def test_interpret_returns_three_parts(self):
        tokens, grammar, ignore = interpret('start: A\nA: "a"')
        assert 'start' in grammar
        assert isinstance(tokens, dict)
        assert isinstance(ignore, dict)

    def test_interpret_mode_switching(self):
        tokens, grammar, ignore = interpret('''
start: A
A: "a" -> +sub

#sub
B: "b" -> -

#other
C: "c"
        ''')
        assert 'sub' in tokens
        assert 'other' in tokens

    def test_interpret_ignore_per_mode(self):
        _, _, ignore = interpret('''
start: A
A: "a"

#m
B: "b"
%ignore " "
        ''')
        assert 'm' in ignore

    def test_interpret_reset_mode_operation(self):
        """The `--` operation should produce a reset (0) action token."""
        tokens, _, _ = interpret('''
start: A
A: "a" -> --
        ''')
        # the action list for "a" should end with 0 (reset marker)
        action = tokens[''][0][1]
        assert 0 in action


# ── Boho with multiple ignored descriptions ──────────────


class TestBohoIgnoreVariations:

    def test_multiple_single_char_ignores(self):
        """Multiple single-char ignores all funnel into the lexer's
        per-mode ignore list."""
        b = Boho('''
start: A+
A: "a"
%ignore " "
%ignore ","
        ''')
        tree = b('a a,a, a')
        assert tree.name == 'start'

    def test_multiple_multi_char_ignores(self):
        """Multiple non-single-char ignores all funnel into the parser
        ignore list."""
        b = Boho('''
start: A+
A: "a"
%ignore "::"
%ignore "##"
        ''')
        tree = b('a::a##a')
        assert tree.name == 'start'


# ── Helpers ──────────────────────────────────────────────


def walk(node):
    yield node
    if isinstance(node, Tree):
        for child in node:
            yield from walk(child)
