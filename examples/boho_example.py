from boho import Boho

grammar = '''
start: a+

a: b* c

b: "b"
c: "c"

'''

text = "bbcbbccc"

b = Boho(grammar, log=True)

print(b(text, log=True).pretty())
