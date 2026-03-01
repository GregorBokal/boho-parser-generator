from boho import Boho

grammar = r'''
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

'''
b = Boho(grammar)
r = b(grammar)

print(r.pretty())
