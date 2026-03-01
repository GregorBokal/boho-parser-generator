from boho import Boho
from boho.interpreter import Interpreter

grammar = '''

start:   sum
  
sum: sum "+" prod
   | prod   
  
prod: prod "*" INT
    | INT  
  
INT: @INT

%ignore " "

'''


class MyInterpreter(Interpreter):

    def start(self, tree):
        print(self(tree[0]))

    def sum(self, tree):
        return sum([self(c) for c in tree])

    def prod(self, tree):
        a = int(self(tree[0]))
        if len(tree) > 1:
            return a * int(self(tree[1]))
        else:
            return a


b = Boho(grammar)
interpreter = MyInterpreter()

while i := input('Enter an expression with addition and multiplication:'):
    tree = b(i)
    interpreter(tree)
