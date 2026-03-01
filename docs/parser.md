# Parser

---

## Overview

The parser's task is to organize **_tokens_** into
an **_abstract syntax tree_**. The Boho parser
builds the tree bottom-up (SHIFT-REDUCE) based on
**_instructions_** for a finite automaton.

## Preparing instructions

Instructions for the parser must be provided as a
dictionary, organized according to the following
structure:

```
// Root dictionary
instructions: '{' entries '}'
entries: (ignore | state) (',' state)*

// Terminals to ignore if they appear unexpectedly.
ignore: "''" ':' '[' @STR (',' @STR)* ']'

state: @STR ':' '{' option (',' option)* '}'

option: @STR ':' action

/*
An action must be defined for:
 - every expected terminal
 - every nonterminal that can begin with
   one of the expected terminals
*/

action: True  // End of analysis (accept)
      | @STR  // Push onto stack (SHIFT)
      | '(' @INT ',' @STR ')'  // Reduce (REDUCE)
```

In plain English:

* The **_root dictionary_** is itself a description
  of the parser's finite automaton. Its keys are
  **_state_** names, and its values are also
  dictionaries that describe each state in detail.
  Analysis starts in state `'0'` by default (this
  can be changed outside the instructions).
* A **_state_** is a dictionary where all symbols
  (terminals and nonterminals) that can follow in a
  given context are mapped to an **_action_** to
  be performed.
* An **_action_** can be:
    * `bool` = end of analysis (accept)
    * `str` = push onto stack (SHIFT); the string
      specifies the name of the state where analysis
      should continue (e.g. `'1'`, `'2'`)
    * `tuple` = reduce (REDUCE);
        * the first element (type `int`) is the
          number of symbols to reduce into a new
          nonterminal.
        * the second element (type `str`) is the
          name of the new nonterminal.

### Instructions example

Instructions for the grammar ...

```
start: read
     | write

read: "get" variable

write: "put" variable

variable: NAME

NAME: /\w+/
```

... are as follows:

```python
instructions = {
    '0': {'"get"': '1',
          '"put"': '2',
          'read': '3',
          'write': '3',
          'statement': '4'},
    '1': {'NAME': '5', 'variable': '6'},
    '2': {'NAME': '5', 'variable': '7'},
    '3': {'$': (1, 'statement')},
    '4': {'$': True},
    '5': {'$': (1, 'variable')},
    '6': {'$': (2, 'read')},
    '7': {'$': (2, 'write')}
}
```

## Default start state

The parser starts analysis in state `'0'` by
default. This can be changed with the `start`
argument when creating the parser:

```python
parser = Parser(instructions, start='initial')
```

## Special cases

### Ignoring terminals

If the instructions contain a list of terminal
names under the `''` key, the parser will silently
skip those terminals when they appear unexpectedly
(instead of raising an error).

```python
instructions = {
    '': ['SPACE', 'COMMENT'],  # Ignore if they appear unexpectedly.
    '0': {...},
    ...
}
```

### Default action (empty key in a state)

If a state contains an empty key `''`, that action
is executed when the parser encounters a terminal
that is not explicitly listed. This allows writing
more compact instructions.

```python
'3': {
    '$': (1, 'statement'),
    '': '5'  # For all other terminals, go to state 5.
}
```

### Auxiliary nonterminals

Auxiliary nonterminals have names that start with
an underscore followed by a lowercase letter
(e.g. `_list`). Their special property is that they
**do not appear as a separate node** in the final
tree — instead, their children are promoted directly
into the parent node.

This is useful for repetitive patterns (e.g. lists)
where intermediate nodes are not desired.

Example: given a grammar for a list of names ...

```
list: NAME _tail
_tail: "," NAME _tail
     |
```

... the input `a, b, c` produces:

```
list:
  NAME a
  NAME b
  NAME c
```

rather than the deeper nesting:

```
list:
  NAME a
  _tail:
    NAME b
    _tail:
      NAME c
```

### Fake terminals

Fake terminals have names that ends with an
underscore
(e.g. `VALUE_`). Even though they are defined
using a reduce action (making them formally
nonterminals), during tree construction they
behave like terminals: all their children are
**merged into a single token** whose value is the
concatenation of all children's values.

This is useful when you want to compose a single
token from multiple tokens. Example: given a
rule for a compound value ...

```
VALUE_: NAME "=" NAME
```

... the input `a = b` produces the token
`Token(name='VALUE_', value='ab')` instead of a
tree node with children.

### Auxiliary  terminals

During a reduce operation, the parser automatically
removes terminals whose name starts with `"`, `'`,
`/` or `_`. These are unnamed terminals (e.g. `"get"`,
`"="`) or named terminals with name that starts with
`_` (e. g. `_TERMINAL`) that serve only for pattern
recognition and are not needed in the final tree.

## Error handling

When an unexpected terminal is encountered, a
`SyntaxError` is raised with an informative message
that includes:

* the expected terminals for the current state,
* the line and column where the error occurred,
* a printout of the problematic line with a
  caret (`^`) pointing to the error.

## Usage example

```python
from boho.parser import Parser
from boho.objects import Token

instructions = {
    '0': {'"get"': '1',
          '"put"': '2',
          'read': '3',
          'write': '3',
          'statement': '4'},
    '1': {'NAME': '5', 'variable': '6'},
    '2': {'NAME': '5', 'variable': '7'},
    '3': {'$': (1, 'statement')},
    '4': {'$': True},
    '5': {'$': (1, 'variable')},
    '6': {'$': (2, 'read')},
    '7': {'$': (2, 'write')}
}

tokens = [
    Token('"get"', 'get'),
    Token('NAME', 'x'),
]

parser = Parser(instructions)
tree = parser(tokens)

print(tree.pretty())
# statement:
#   read:
#     variable:
#       NAME x
```
