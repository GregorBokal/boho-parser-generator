# The boho metalanguage

The boho metalanguage is used to describe grammars and terminals, from which instructions for lexical and syntactic
analysis are automatically generated.

## Comments

Comments follow C-style syntax: `// ...` until end of line, or `/* ... */` spanning multiple lines.

## Terminal descriptions

Terminals can be described in three ways:

- **String literal** — an exact character sequence (e.g. `"if"`, `'='`).
- **Regular expression** — enclosed in slashes (e.g. `/\d+/`).
- **Built-in description** — prefixed with `@` (e.g. `@STR`, `@INT`, `@FLOAT`).

These can be used directly in grammar rules as *unnamed terminals*, which are pruned from the syntax tree.

To retain a terminal in the tree, it must be *named* (uppercase name):

```
PLUS: "+"               // String literal
NATURAL_NUMBER: /\d+/   // Regular expression
INTEGER: @INT            // Built-in description
```

If the name starts with an underscore (e.g. `_LONG_COMMENT`), the terminal is pruned from the tree despite being named.

## Grammar rules

Nonterminals are described with `nonterminal: description` (lowercase name). Alternatives are separated by `|`:

```
variable: NAME "=" value
value: NAME | NUMBER
```

EBNF extensions are supported (following Lark's conventions):

```
text: paragraph+              // + = one or more repetitions
paragraph: sentence* "\n"     // * = zero or more repetitions
sentence: clause (conj clause)*  // parentheses for grouping
simple: subject? predicate    // ? = optional
```

The `->` annotation can be used to name individual alternatives inline:

```
clause: subject? predicate object? -> simple
      | INTERJECTION+              -> exclamation
```

### Fake terminals

Fake terminals (uppercase name ending with an underscore, e.g. `COMMENT_`) are described like nonterminals but are
collapsed into a single token during analysis. They enable recognition of structures that regular expressions cannot
describe (e.g. nested comments).

## Lexer mode switching

Following ANTLR's approach, a modal lexer is supported. After a terminal description, `->` specifies operations on the
mode stack:

| Syntax     | Effect               |
|------------|----------------------|
| (none)     | no change            |
| `-> +mode` | push mode onto stack |
| `-> -`     | pop top of stack     |
| `-> mode`  | replace top of stack |
| `-> -2`    | pop 2 modes          |
| `-> --`    | clear the stack      |

Modes are declared with `#mode_name` on a separate line. Terminals before the first `#` statement belong to all modes.
Example:

```
LPAREN: "(" -> +number
RPAREN: ")" -> -

#text
WORD: /[^(]+/

#number
INT: /-?\d+/ -> operation
```

## Ignoring tokens

The `%ignore TERMINAL` statement tells the parser which tokens to ignore (typically whitespace, comments). If ignoring a
single-character string literal, the lexer itself handles the ignoring — so with a modal lexer, the placement of
`%ignore` relative to `#` statements matters.

## The boho language described in boho

```
START: "/*" -> +comment

#boho

start: _statement+

_statement: _NL
          | U_NAME ":" description operations? -> terminal
          | _name ":" options                  -> nonterminal
          | "#" L_NAME                         -> mode
          | "%ignore" (description | U_NAME)   -> ignore
          | _LONG_COMMENT_

description: STR
           | REGEX
           | AT
operations: "->" _operation+
_operation: P L_NAME -> push_mode
          | "-" N?     -> pop_mode
          | "--"       -> reset_mode
          | L_NAME     -> change_mode

_name: L_NAME | F_NAME
options: option (_OR option)*
option: units ("->" _name)?
units: unit+
unit: atom quantifier?
atom: U_NAME | _name | description
    | "(" options ")"
quantifier: Q | S | P

Q: "?"
S: "*"
P: "+"

L_NAME: /_?[a-z][a-z_]*/
F_NAME: /_?[A-Z][A-Z_]*_/
U_NAME: /[A-Z_]*[A-Z]/

STR: @STR
REGEX: /\/([^\/*]|\\\/|\\\*)([^\/]|\\\/)*\//
AT: /@[A-Z_]*/
N: /\d+/

_OR: /(\n\s*)?\|\s*/
_NL: /\n\s*/


%ignore " "
%ignore /\/\/([^\n]*[^\/])?/

#comment

_LONG_COMMENT_: START _content* STOP
_content: CONTENT | _LONG_COMMENT_
CONTENT: /([^*\/])+|\\*|\//
STOP: "*/" -> -
```