# Lexer

---

## Overview

The lexer's task is to split **_text_** into
**_tokens_** (based on given **_instructions_**
for a finite automaton).

## Preparing instructions

Instructions for the lexer must be provided as a
dictionary, organized according to the following
structure:

```
// Root dictionary
instructions: '{' entries '}'
entries: (default | mode) (',' mode)*

// Default mode declaration
default: "''" ':' @STR

// Description of a specific mode
mode: @STR ':' finite_automaton

finite_automaton: '{' (ignore | state) (',' state)* '}'

// List of characters that can appear between tokens.
ignore: "''" ':' '[' @STR (',' @STR)* ']'

state: @STR ':' '{' option (',' option)* '}'

option: char_desc ':' action

char_desc: @STR // description using a regular expression
         | "''" // default option

action: @STR // Continuing a token (index of next state)
      | '[' token_name operations? ']' // finishing a token

token_name: @STR

operations: (',' operation) // Changes on the mode stack

operation: @STR // Push a mode onto the stack
         | '0'  // Clear the stack
         | /d+/ // Pop modes from the top of the stack.
```

In plain English:

* The **_root dictionary_** has mode names as
  keys (the lexer supports switching between
  different lexing modes), while the values
  represent the **_finite automaton_** instructions
  for each mode.
* A **_finite automaton_** is described by a
  dictionary of **_states_** and an optional list
  of characters to be ignored if they unexpectedly
  appear between tokens.
* A **_state_** is a dictionary where expected
  characters (described using regular expressions,
  or an empty string for the default option) are
  mapped to an **_action_** to be performed.
* An **_action_** can be:
    * `str` = continuing a token; the string
      specifies the name of the state where analysis
      should continue (e.g. `'1'`, `'2'`).
    * `list` = finishing a token;
        * the first element (type `str`) is the
          token name.
        * remaining elements represent **operations
          on the mode stack** performed when the
          token is finalized. These can be:
            * `str` = push a new mode onto the stack.
            * `0` = clear the stack.
            * `int` (> 0) = pop a given number of
              modes from the top of the stack.

### Simple instructions example

```python
instructions = {
    '': {  # The only lexing current_mode
        '': [' '],  # Ignore spaces
        '0': {  # Initial state (0).
            'h': '1'  # If we see h, go to state 1.
        },
        '1': {  # State 1
            '[aeiou]': '1',  # On aeiou, stay in state 1.
            '': ['ha']  # Otherwise, finish the 'ha' token.
        }
    }
}
```

### Advanced instructions example

```python
instructions = {
    '': 'text_mode',  # Default current_mode
    'text_mode': {
        '0': {
            '[^(]': '1',
            r'\(': '2'
        },
        '1': {
            '[^(]': '1',
            '': ['text']
        },
        '2': {
            # Finish '(' and push a new current_mode onto the stack.
            '': ['(', 'number_mode']
        }
    },
    'number_mode': {
        # In this current_mode we ignore spaces
        '': [' '],
        '0': {
            r'\d': '1',
            r'\(': '2',
            r'\)': '3'
        },
        '1': {
            r'\d': '1',
            '': ['number']
        },
        '2': {
            '': ['(', 'number_mode']
        },
        '3': {
            # Finish ')' and pop the top current_mode from the stack.
            '': [')', 1]
        }
    }
}
```

## Default start mode

The lexer determines the start mode using one of
three methods (by priority):

1. Pass it as the `start_mode` argument when
   creating the lexer: `Lexer(instructions, start_mode='name')`.
2. Specify the default mode in the instructions
   under the `''` key: `{'': 'mode_name', ...}`.
3. The first mode in the instructions dictionary
   is used.

## Error handling

When the lexer encounters an unexpected character,
it raises a `SyntaxError` with an informative
message that includes:

* the expected characters for the current state,
* the line and column where the error occurred,
* a printout of the problematic line with a
  caret (`^`) pointing to the error.

If the input ends with an unfinished token, the
lexer checks whether the current state contains a
default option (`''`) that finishes the token. If
not, it raises a `SyntaxError` describing the
unfinished token.

## Usage example

```python
from boho.lexer import Lexer

instructions = {
    '': 'text_mode',
    'text_mode': {
        '0': {'[^(]': '1', r'\(': '2'},
        '1': {'[^(]': '1', '': ['text']},
        '2': {'': ['(', 'number_mode']}
    },
    'number_mode': {
        '': [' '],
        '0': {r'\d': '1', r'\(': '2', r'\)': '3'},
        '1': {r'\d': '1', '': ['number']},
        '2': {'': ['(', 'number_mode']},
        '3': {'': [')', 1]}
    }
}

text = '123 is text, (123) is a number.'

lexer = Lexer(instructions)
print(lexer(text))
# [Token(name='text', value='123 is text, ', line=0, col=0),
#  Token(name='(', value='(', line=0, col=13),
#  Token(name='number', value='123', line=0, col=14),
#  Token(name=')', value=')', line=0, col=17),
#  Token(name='text', value=' is a number.', line=0, col=18)]
```
