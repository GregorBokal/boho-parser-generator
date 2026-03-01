import os
import time
from pprint import pprint

from boho.lexer import Lexer
from boho.parser import Parser
from boho.lexer_generator import generate as prepare_lex
from boho.parser_generator import generate as prepare_pars
from json import dump, load

terminals = {
    'boho': [
                (a, [a]) for a in [
            '":"',
            '"#"',
            '"%ignore"',
            '"->"',
            '"-"',
            '"--"',
            '"("',
            '")"',
            r'///([^\n]*[^/])?/'
        ]
            ] + [
                (r'/\n\s*/', ['_NL']),
                ('"?"', ['Q']),
                ('"*"', ['S']),
                ('"+"', ['P']),
                ('/_?[a-z][a-z_]*/', ['L_NAME']),
                ('/_?[A-Z][A-Z_]*_/', ['F_NAME']),
                ('/[A-Z_]*[A-Z]/', ['U_NAME']),
                ('@STR', ['STR']),
                (r'/\/([^/*]|\\\/|\\\*)([^/]|\\\/)*\//', ['REGEX']),
                ('/@[A-Z_]*/', ['AT']),
                (r'/\d+/', ['N']),
                (r'/(\n\s*)?\|\s*/', ['_OR']),
                ('"/*"', ['START', 'comment'])
            ],
    'comment': [
        ('"/*"', ['START', 'comment']),
        ('"*/"', ['STOP', 1]),
        ('/([^*/])+|\\*|//', ['CONTENT'])
    ]
}

grammar = {
    'start': [('_statements',)],
    '_statements': [
        ('_statements', '_statement'),
        ('_statement',)
    ],
    '_statement': [
        (f'_NL',),
        ('terminal',),
        ('nonterminal',),
        ('mode',),
        ('ignore',),
        ('_LONG_COMMENT_',)
    ],
    'terminal': [
        ('U_NAME', '":"', 'description'),
        ('U_NAME', '":"', 'description', 'operations')
    ],
    'description': [('STR',), ('REGEX',), ('AT',)],
    'operations': [('"->"', '_operations')],
    '_operations': [
        ('_operations', '_operation'),
        ('_operation',)
    ],
    '_operation': [
        ('push_mode',),
        ('pop_mode',),
        ('reset_mode',),
        ('change_mode',)
    ],
    'push_mode': [('P', 'L_NAME')],
    'pop_mode': [
        ('"-"',),
        ('"-"', 'N')
    ],
    'reset_mode': [('"--"',)],
    'change_mode': [('L_NAME',)],
    'nonterminal': [('_name', '":"', 'options')],
    '_name': [('L_NAME',), ('F_NAME',)],
    'options': [('_options',)],
    '_options': [
        ('_options', '_OR', 'option'),
        ('option',)
    ],
    'option': [
        ('units', '"->"', '_name'),
        ('units',)
    ],
    'units': [('_more_units',)],
    '_more_units': [
        ('_more_units', 'unit'),
        ('unit',)
    ],
    'unit': [
        ('atom', 'quantifier'),
        ('atom',)
    ],
    'atom': [
        ('U_NAME',),
        ('_name',),
        ('description',),
        ('"("', 'options', '")"')
    ],
    'quantifier': [('Q',), ('S',), ('P',)],
    '_LONG_COMMENT_': [('START', '_content', 'STOP')],
    '_content': [('_content', '_unit'), ('_unit',)],
    '_unit': [('CONTENT',), ('_LONG_COMMENT_',)],
    'mode': [('"#"', 'L_NAME')],
    'ignore': [
        ('"%ignore"', 'description'),
        ('"%ignore"', 'U_NAME'),
    ]
}

if 'boho_grammar.json' in os.listdir():
    with open('boho_grammar.json', 'r') as f:
        kind, li, pi = load(f)
else:
    t = time.time()
    li = prepare_lex(terminals)
    pprint(li)
    li['boho'][''] = [' ']
    l = time.time()
    pi = prepare_pars(grammar)
    pi[''] = [r'///([^\n]*[^/])?/']
    p = time.time()
    print(f'Lexer: {sum(len(li[m]) for m in li)} ({l - t} s), Parser: {len(pi)} ({p - l} s)')
    with open('../boho/boho_grammar.json', 'w') as f:
        dump(['LR1', li, pi], f)

lexer = Lexer(li)
parser = Parser(pi)

text = '''
start: _stavek+

_stavek: "\\n"
       | V_IME ":" opis operacije?  -> terminal
       | _ime ":" moznosti          -> neterminal
       | "#" M_IME                  -> nacin
       | "%ignore" (opis | V_IME)   -> ignoriranje
       | _DOLG_KOMENTAR_

opis: NIZ
    | REGEX
    | AFNA
operacije: "->" _operacija+
_operacija: "+" M_IME  -> dodajanje
          | "-" N?     -> brisanje
          | "--"       -> izpraznitev
          | M_IME      -> menjava

_ime: M_IME | L_IME
moznosti: moznost (_ALI moznost)*
moznost: enote ("->" _ime)?
enote: enota+
enota: atom oznaka?
atom: V_IME | _ime | opis
     | "(" moznosti ")"
oznaka: "?" | "*" | "+"

M_IME: /_?[a-z][a-z_]*/
L_IME: /_?[A-Z][A-Z_]*_/
V_IME: /_?[A-Z][A-Z_]*/

NIZ: @STR
REGEX: /\\/([^\\/]|\\\\\/)\\//
AFNA: /@[A-Z_]*/
N: /\\d+/

_ALI: /\s*\|\s*/

_DOLG_KOMENTAR_: "/*" (VSEBINA | _DOLG_KOMENTAR_)* "*/"
VSEBINA: /([^\*]|\*[^\/])+/

%ignore " "
%ignore /\/\/[^\\n]/
'''
tokens = lexer(text)
tree = parser(tokens)

print(tree.pretty())
