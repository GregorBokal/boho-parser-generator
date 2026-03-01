# Parser Generator

---

## Overview

The parser generator prepares instructions
for syntactic analysis with an LR(1) parser
based on a given grammar.

## Input

The input grammar must be described as a
dictionary where the keys are nonterminals
and the values are lists of possible
productions (described using tuples):

```python
grammar = {
    'start': [
        ('start', '"+"', 'term'),
        ('term',)
    ],
    'term': [
        ('term', '"*"', 'atom'),
        ('atom',)
    ],
    'atom': [('@INT',)]
}
```

By default, the start nonterminal should be
named `'start'`, but a different name can
also be used — it just needs to be specified
when calling the generation function.

## Usage example

```python
from boho.parser_generator import generate

grammar = {
    'expr': [
        ('expr', '"+"', 'term'),
        ('term',)
    ],
    'term': [
        ('term', '"*"', 'atom'),
        ('atom',)
    ],
    'atom': [('@INT',)]
}

generate(
    grammar,
    start='expr',  # These are
    kind='LR1',  # optional
    log=True  # parameters.
)
```
