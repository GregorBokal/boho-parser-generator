# Lexer Generator

---

## Overview

The lexer generator produces a dictionary of lexer
instructions based on terminal descriptions (the
structure of the instructions is described in the
lexer documentation).

## Input

For each lexical mode, you must provide a list of
`(description, action)` pairs, where:

- `action` (type `list`) is the action to be
  performed when the lexer recognizes a token (see
  the lexer documentation).
- `description` (type `str`) is the value used to
  first generate a finite automaton for recognizing
  that particular token. A description can be given
  as:
    - A **string literal** enclosed in double quotes, e.g. `'"ABC"'`.
    - A **regular expression** enclosed in forward slashes, e.g. `'/A[BC]/'`.
    - The **name** of a prepared description preceded by @, e.g. `'@INT'`.

## Usage example

```python
from boho.lexer_generator import generate

tokens = {
    'mode_1': [
        ('"AB"', ['AB', 1, 'mode_1']),
        ('"ABC"', ['ABC'])
    ],
    'mode_2': [
        ('@INT', ['INT']),
        (r'/-?\d*\.\d+/', ['FLOAT', 1, 'mode_2'])
    ]
}

generate(tokens, log=True)

```
