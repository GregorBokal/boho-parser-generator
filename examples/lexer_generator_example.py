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
