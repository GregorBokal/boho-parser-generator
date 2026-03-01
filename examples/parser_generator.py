from boho.parser_generator import generate

grammar = {
    'start': [
        ('start', '"+"', 'product'),
        ('product',)
    ],
    'product': [
        ('product', '"*"', 'atom'),
        ('atom',)
    ],
    'atom': [('@INT',)]
}

generate(grammar, log=True)
