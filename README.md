# Boho

A self-hosting parser generator for Python. Define your grammar in a concise EBNF-based metalanguage and Boho will generate a modal lexer (DFA-based) and an LR(1) parser that produce a clean syntax tree.

## Installation

```bash
pip install boho
```

## Quick start

```python
from boho import Boho
from boho.interpreter import Interpreter

grammar = '''
start: sum

sum: sum "+" prod
   | prod

prod: prod "*" INT
    | INT

INT: @INT

%ignore " "
'''

b = Boho(grammar)
tree = b("2 + 3 * 4")
print(tree.pretty())
```

Output:

```
start:
  sum:
    sum:
      prod:
        'INT' '2'
    prod:
      prod:
        'INT' '3'
      'INT' '4'
```

### Writing an interpreter

Subclass `Interpreter` and define methods matching your nonterminal names:

```python
class Calc(Interpreter):
    def start(self, tree):
        return self(tree[0])

    def sum(self, tree):
        return sum(self(c) for c in tree)

    def prod(self, tree):
        result = int(self(tree[0]))
        for i in range(1, len(tree)):
            result *= int(self(tree[i]))
        return result

calc = Calc()
print(calc(tree))  # 14
```

## The Boho metalanguage

### Terminal definitions

Terminals are named in `UPPER_CASE` and can be described three ways:

```
PLUS: "+"               // string literal
NUMBER: /\d+(\.\d+)?/   // regular expression
STRING: @STR             // built-in description (@INT, @FLOAT, @STR)
```

Terminal descriptions can also be used directly (unnamed) in grammar rules -- they will be pruned from the syntax tree.

Prefixing a terminal name with `_` (e.g. `_WHITESPACE`) prunes it from the tree despite being named.

### Grammar rules

Nonterminals use `lower_case` names. Alternatives are separated with `|`:

```
value: NAME | NUMBER
assignment: NAME "=" value
```

EBNF extensions:

```
items: item+              // one or more
list: (item ",")*  item   // zero or more (with grouping)
optional: modifier?       // optional
```

Inline aliases with `->`:

```
expr: term "+" term -> addition
    | term "-" term -> subtraction
```

### Fake terminals

A name like `COMMENT_` (uppercase ending with `_`) defines a fake terminal -- described like a nonterminal but collapsed into a single token. Useful for structures that regular expressions cannot describe (e.g. nested block comments).

### Lexer modes

Following ANTLR's approach, a modal lexer is supported. Terminals before the first `#mode` belong to all modes.

```
LBRACE: "{" -> +inner    // push mode
RBRACE: "}" -> -         // pop mode

#inner
CONTENT: /[^{}]+/
```

| Syntax     | Effect               |
|------------|----------------------|
| `-> +mode` | push mode onto stack |
| `-> -`     | pop one mode         |
| `-> -N`    | pop N modes          |
| `-> --`    | clear the stack      |
| `-> mode`  | replace top of stack |

### Ignoring tokens

```
%ignore " "
%ignore /\/\/[^\n]*/    // ignore line comments
```

## Project structure

```
boho/
  __init__.py            # exports the Boho class
  boho.py                # main orchestrator
  lexer.py               # modal finite-automaton lexer
  lexer_generator.py     # terminal descriptions -> lexer DFA
  parser.py              # LR(1) shift-reduce parser
  parser_generator.py    # grammar -> LR(1) parse tables
  grammar_interpreter.py # interprets the Boho metalanguage
  interpreter.py         # base Interpreter class (visitor pattern)
  objects.py             # Token, Tree, LR1Item dataclasses
  regex.py               # regex-to-DFA via greenery
  grammars.py            # pre-compiled Boho grammar tables
docs/                    # English documentation
slo-dokumentacija/       # Slovenian documentation
examples/                # usage examples
tests/                   # test suite
```

## How it works

1. Your grammar string is parsed by Boho's own (bootstrapped) parser.
2. Terminal descriptions are compiled into merged DFAs for a modal lexer.
3. Grammar rules are compiled into LR(1) parse tables.
4. At runtime, input text is tokenized by the lexer and then parsed into a `Tree` of `Token` leaves.

Boho is self-hosting -- its own metalanguage is specified in Boho (see `examples/boho_in_boho.py`).

## API

### `Boho(grammar, log=False)`

Create a parser from a grammar string. Set `log=True` to print the generated lexer and parser tables.

### `boho(text, log=False) -> Tree`

Parse input text. Returns a `Tree` with `Token` leaves. Set `log=True` for step-by-step tracing.

### `Tree`

- `tree.name` -- nonterminal name
- `tree.children` -- list of `Tree` / `Token` children
- `tree.value` -- concatenated text of all descendant tokens
- `tree.pretty()` -- indented string representation
- Supports iteration and indexing (`tree[0]`, `for child in tree`)

### `Token`

- `token.name` -- terminal name
- `token.value` -- matched text
- `token.line`, `token.col` -- source location

### `Interpreter`

Base class for tree walkers. Subclass it and define methods named after your nonterminals. The default behavior for unhandled nodes: tokens return their value, trees return a list of children's results.

## Dependencies

- [greenery](https://github.com/qntm/greenery) -- regex-to-FSM conversion
- Python 3.10+ (uses `match` statements and `X | Y` type unions)

## License

MIT
