from boho.parser import Parser
from boho.objects import Token

instructions = {
    '0': {
        'NAME': '1',
        '_statement': '2',
        'start': '3'
    },
    '1': {
        '"="': '4'
    },
    '2': {
        '$': (1, 'start')
    },
    '3': {
        '$': True
    },
    '4': {
        'NAME': '5',
        'VALUE_': '6',
        '_statement': '2',
        'start': '7'
    },
    '5': {
        '"="': '4',
        '$': (1, 'VALUE_')
    },
    '6': {
        '$': (3, '_statement')
    },
    '7': {
        '$': (1, 'VALUE_')
    }
}

tokens = [
    Token('NAME', 'a'),
    Token('"="', '='),
    Token('NAME', 'b'),
    Token('"="', '='),
    Token('NAME', 'c'),
    Token('"="', '='),
    Token('NAME', 'd')
]

parser = Parser(instructions)
parser(tokens, log=True)
