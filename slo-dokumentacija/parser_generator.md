# Parser-generator

---

## Opis

Parser-generator na podlagi
dane slovnice pripravi navodila
za sintaktično analizo z LR(1)
parserjem.

## Vhodni podatki

Vhodna slovnica mora biti opisana
kot slovar, kjer so ključi neterminali,
vrednosti pa seznami možnih produkcij
(ki pa so opisane z mnogotericami):

```python
grammar = {
    'start': [
        ('start', '"+"', 'clen'),
        ('clen',)
    ],
    'clen': [
        ('clen', '"*"', 'atom'),
        ('atom',)
    ],
    'atom': [('@INT',)]
}
```

Zaželeno je, da se izhodiščni
terminal imenuje `'start'`,
vendar se lahko uporabi tudi
katero drugo ime, ki pa ga
je treba navesti pri klicu
funkcije za generiranje
pravil.

## Primer uporabe

```python
from boho.parser_generator import generate

grammar = {
    'izraz': [
        ('izraz', '"+"', 'clen'),
        ('clen',)
    ],
    'clen': [
        ('clen', '"*"', 'atom'),
        ('atom',)
    ],
    'atom': [('@INT',)]
}

generate(
    grammar,
    start='izraz',  # To so
    kind='LR1',  # neobvezni
    log=True  # parametri.
)
```
