from boho.lexer import Lexer

simple_instructions = {
    '': {  # The only lexing current_mode
        '': [' '],  # Characters to ignore
        '0': {  # State 0
            'h': '1'
        },
        '1': {  # State 1
            '[aeiou]': '1',
            '': ['ha'],
        },
    }
}

simple_lexer = Lexer(simple_instructions)

# [Token(name='ha', value='haa', line=0, col=0), Token(name='ha', value='haa', line=0, col=3), Token(name='ha', value='he', line=0, col=6), Token(name='ha', value='hia', line=0, col=8)]
print(simple_lexer('haa haa hehia', log=True))

complex_instructions = {
    '': 'text',
    'text': {
        '0': {'[^(]': '1', r'\(': '2'},
        '1': {'[^(]': '1', '': ['text']},
        '2': {'': ['(', 'expression']},
    },
    'expression': {
        '': [' '],
        '0': {r'\d': '1', r'\(': '2', r'\)': '3'},
        '1': {
            r'\d': '1',
            '': ['number'],
        },
        '2': {'': ['(', 'expression']},
        '3': {'': [')', 1]},
    },
}

modal_lexer = Lexer(complex_instructions)
# [Token(name='text', value='00', line=0, col=0), Token(name='(', value='(', line=0, col=2), Token(name='number', value='11', line=0, col=3), Token(name='(', value='(', line=0, col=5), Token(name='number', value='22', line=0, col=6), Token(name='(', value='(', line=0, col=8), Token(name='number', value='33', line=0, col=9), Token(name=')', value=')', line=0, col=11), Token(name='number', value='22', line=0, col=12), Token(name=')', value=')', line=0, col=14), Token(name='number', value='11', line=0, col=15), Token(name=')', value=')', line=0, col=17), Token(name='text', value='00', line=0, col=18)]
print(modal_lexer('00(11 (2 2(33)22)11)00', log=True))
