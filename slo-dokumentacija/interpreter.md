# Tolmač

---

## Opis

Tolmač je namenjen „sprehanjanju“ po sintaktičnem
drevesu in izvajanju želenih akcij. Na voljo je
generičen razred `Interpreter`, na osnovi katerega
se lahko nato naredi tolmač za konkreten jezik.

## Generičen razred

Razred, na katerem so osnovani konkretni tolmači, je sledeč:

```python
class Interpreter:
    def __call__(self, node: Tree | Token):
        # Če implementiramo funkcijo z enakim imenom, kot je ime vozlišča,
        if hasattr(self, node.name):
            # jo uporabimo.
            return getattr(self, node.name)(node)
        # Če take funkcije ni, gre pa za žeton,
        elif isinstance(node, Token):
            # tolmač vrne vrednost žetona
            return node.value
        # Če pa gre za delno drevo (neterminal),
        else:
            # vrne seznam obdelanih podvozlišč
            return [self(p) for p in node.children]
```

## Primer uporabe

```python
from boho.interpreter import Interpreter
from boho.objects import Tree, Token


class Tolmac(Interpreter):

    def start(self, drevo: Tree):
        print(self(drevo[0]))

    def izraz(self, drevo: Tree):
        return sum([self(v) for v in drevo])

    def clen(self, drevo: Tree):
        a = int(self(drevo[0]))
        if len(drevo) > 1:
            return a * int(self(drevo[1]))
        else:
            return a


# Sintaktično drevo za izraz 1 + 2 * 3
# v obliki, kot ga naredi parser:
d = Tree('start', [
    Tree('izraz', [
        Tree('izraz', [
            Tree('clen', [
                Token('INT', '1')
            ])
        ]),
        Tree('clen', [
            Tree('clen', [
                Token('INT', '2')
            ]),
            Token('INT', '3')
        ])
    ])
])

tolmac = Tolmac()
print(d.pretty())
tolmac(d)
```
