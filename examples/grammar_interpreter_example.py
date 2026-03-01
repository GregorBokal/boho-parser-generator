from boho.grammar_interpreter import interpret
from pprint import pprint

text = '''
start: stavek+
stavek: "beri" IME -> beri
      | "pisi" IME -> pisi
IME: /[A-Z]+/

%ignore " "
%ignore IME
'''
pprint(interpret(text))
