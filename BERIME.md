# Boho

Boho je zmogljivo orodje za obdelavo programskih
jezikov. Svojo slovnico opišete v jedrnatem
metajeziku (osnovan na EBNF), Boho pa iz nje
samodejno zgradi modalni lekser (na osnovi DFA) in
LR(1) parser, ki vrneta čisto sintaktično drevo.

## Namestitev

```bash
pip install boho
```

## Hiter začetek

```python
from boho import Boho
from boho.interpreter import Interpreter

grammar = '''
start: vsota

vsota: vsota "+" produkt
     | produkt

produkt: produkt "*" STEVILO
       | STEVILO

STEVILO: @INT

%ignore " "
'''

b = Boho(grammar)
drevo = b("2 + 3 * 4")
print(drevo.pretty())
```

Izpis:

```
start:
  vsota:
    vsota:
      produkt:
        'STEVILO' '2'
    produkt:
      produkt:
        'STEVILO' '3'
      'STEVILO' '4'
```

### Pisanje tolmača

Podedite razred `Interpreter` in definirajte metode, ki se ujemajo z imeni neterminalov:

```python
class Kalkulator(Interpreter):
    def start(self, drevo):
        return self(drevo[0])

    def vsota(self, drevo):
        return sum(self(c) for c in drevo)

    def produkt(self, drevo):
        rezultat = int(self(drevo[0]))
        for i in range(1, len(drevo)):
            rezultat *= int(self(drevo[i]))
        return rezultat


kalk = Kalkulator()
print(kalk(drevo))  # 14
```

## Metajezik Boho

### Definicije terminalov

Terminali se poimenujejo z `VELIKIMI_ČRKAMI` in se opišejo na tri načine:

```
PLUS: "+"               // znakovni niz
STEVILO: /\d+(\.\d+)?/  // regularni izraz
NIZ: @STR               // vgrajen opis (@INT, @FLOAT, @STR)
```

Opise terminalov lahko uporabite tudi neposredno (nepoimenovano) v pravilih slovnice -- v tem primeru se odstranijo iz
sintaktičnega drevesa.

Če imenu terminala dodate predpono `_` (npr. `_PRESLEDEK`), se terminal odstrani iz drevesa, čeprav je poimenovan.

### Pravila slovnice

Neterminali uporabljajo `male_črke`. Alternative ločimo z `|`:

```
vrednost: IME | STEVILO
prirejanje: IME "=" vrednost
```

Razširitve EBNF:

```
elementi: element+               // ena ali več ponovitev
seznam: (element ",")*  element  // nič ali več ponovitev (z združevanjem)
opcijsko: modifikator?           // opcijsko
```

Inline vzdevki z `->`:

```
izraz: člen "+" člen -> seštevanje
     | člen "-" člen -> odštevanje
```

### Lažni terminali

Ime oblike `KOMENTAR_` (velike črke, ki se končajo z `_`) definira lažni terminal -- opisan kot neterminal, a zložen v
en sam žeton. Uporabno za strukture, ki jih regularni izrazi ne morejo opisati (npr. gnezdeni blok komentarji).

### Načini leksičnega analizatorja

Po zgledu ANTLR-ja je podprt modalni leksični analizator. Terminali pred prvim `#način` pripadajo vsem načinom.

```
LEVI_OKLEPAJ: "{" -> +notranji    // dodaj način na sklad
DESNI_OKLEPAJ: "}" -> -           // odstrani način s sklada

#notranji
VSEBINA: /[^{}]+/
```

| Sintaksa    | Učinek               |
|-------------|----------------------|
| `-> +način` | dodaj način na sklad |
| `-> -`      | odstrani en način    |
| `-> -N`     | odstrani N načinov   |
| `-> --`     | izprazni sklad       |
| `-> način`  | zamenjaj vrh sklada  |

### Ignoriranje žetonov

```
%ignore " "
%ignore /\/\/[^\n]*/    // ignoriraj enovrstične komentarje
```

## Struktura projekta

```
boho/
  __init__.py            # izvozi razred Boho
  boho.py                # glavni orkestrator
  lexer.py               # modalni leksični analizator (končni avtomat)
  lexer_generator.py     # opisi terminalov -> DFA za leksični analizator
  parser.py              # LR(1) razčlenjevalnik (shift-reduce)
  parser_generator.py    # slovnica -> LR(1) razčlenjevalne tabele
  grammar_interpreter.py # tolmač metajezika Boho
  interpreter.py         # osnovni razred Interpreter (vzorec obiskovalec)
  objects.py             # podatkovni razredi Token, Tree, LR1Item
  regex.py               # pretvorba regex v DFA prek greenery
  grammars.py            # vnaprej prevedene tabele slovnice Boho
docs/                    # angleška dokumentacija
slo-dokumentacija/       # slovenska dokumentacija
examples/                # primeri uporabe
tests/                   # testi
```

## Kako deluje

1. Vaš niz s slovnico razčleni Bohov lastni (samogostiteljski) razčlenjevalnik.
2. Opisi terminalov se prevedejo v združene DFA-je za modalni leksični analizator.
3. Pravila slovnice se prevedejo v LR(1) razčlenjevalne tabele.
4. Med izvajanjem leksični analizator tokenizira vhodni tekst, razčlenjevalnik pa ga razčleni v `Tree` z listi `Token`.

Boho je samogostiteljski -- njegov lastni metajezik je opisan v Bohu samem (glej `examples/boho_in_boho.py`).

## API

### `Boho(grammar, log=False)`

Ustvari razčlenjevalnik iz niza s slovnico. `log=True` izpiše generirane tabele.

### `boho(text, log=False) -> Tree`

Razčleni vhodni tekst. Vrne `Tree` z listi `Token`. `log=True` za sledenje po korakih.

### `Tree`

- `tree.name` -- ime neterminala
- `tree.children` -- seznam otrok (`Tree` / `Token`)
- `tree.value` -- zlepljeno besedilo vseh potomcev
- `tree.pretty()` -- zamaknjen izpis
- Podpira iteracijo in indeksiranje (`tree[0]`, `for child in tree`)

### `Token`

- `token.name` -- ime terminala
- `token.value` -- ujemajoče besedilo
- `token.line`, `token.col` -- položaj v izvoru

### `Interpreter`

Osnovni razred za obhod drevesa. Podedite ga in definirajte metode, poimenovane po vaših neterminalih. Privzeto
obnašanje za neobravnavana vozlišča: žetoni vrnejo svojo vrednost, drevesa vrnejo seznam rezultatov otrok.

## Odvisnosti

- [greenery](https://github.com/qntm/greenery) -- pretvorba regularnih izrazov v končne avtomate
- Python 3.10+ (uporablja `match` stavke in `X | Y` tipske unije)

## Licenca

MIT
