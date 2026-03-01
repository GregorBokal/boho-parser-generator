# Parser

---

## Opis

Naloga parserja je **_žetone_** organizirati
v **_abstraktno sintaktično drevo_**.
Boho parser gradi drevo od spodaj navzdol
(SHIFT-REDUCE) na podlagi **_navodil_** za
končni avtomat.

## Priprava navodil

Navodila za parser morajo biti podana kot
slovar, urejen po sledeči strukturi:

```dockerfile
// Izhodiščni slovar
navodila: '{' elementi '}'
elementi: (ignoriraj | stanje) (',' stanje)*

// Terminali, ki jih ignoriramo, če se nepričakovano pojavijo.
ignoriraj: "''" ':' '[' @STR (',' @STR)* ']'

stanje: @STR ':' '{' moznost (',' moznost)* '}'

moznost: @STR ':' akcija

/*
Akcijo določimo za:
 - vsak pričakovan terminal
 - vsak neterminal, ki se lahko začne
   s katerim od pričakovanih terminalov
*/

akcija: True  // Konec analize
      | @STR  // Dodajanje na sklad (SHIFT)
      | '(' @INT ',' @STR ')'  // Predelovanje (REDUCE)
```

Še po slovensko:

* **_Izhodiščni slovar_** je sam po sebi opis za
  končni avtomat parserja. Ključi tega slovarja
  so imena **_stanj_**, vrednosti pa tudi tokrat slovar
  za podrobnejši opis stanja. Analiza se privzeto
  začne v stanju `'0'` (lahko pa izven navodil
  nastavimo tudi drugače):
* **_stanje_** je slovar, kjer je za vse simbole
  (terminale in neterminale), ki lahko v danem
  kontekstu sledijo, določena **_akcija_**, ki se ob tem izvede.
* **_akcija_** je lahko:
    * `bool` = zaključek analize
    * `str`= dodajanje na sklad (SHIFT); z nizom
      navedemo ime stanja, v katerem naj se
      analiza nadaljuje (npr. `'1'`, `'2'`)
    * `tuple` = predelovanje (REDUCE);
        * prvi element (tipa `int`) število simbolov,
          ki jih je treba predelati v nov neterminal.
        * drugi element (tipa `str`) predstavlja
          ime novega neterminala.

### Primer navodil

Navodila za slovnico ...

```dockerfile
start: branje
     | pisanje

branje: "beri" spremenljivka

pisanje: "piši" spremenljivka

spremenljivka: IME

IME: /\w+/
```

... so sledeča:

```python
navodila = {
    '0': {'"beri"': '1',
          '"piši"': '2',
          'branje': '3',
          'pisanje': '3',
          'stavek': '4'},
    '1': {'IME': '5', 'spremenljivka': '6'},
    '2': {'IME': '5', 'spremenljivka': '7'},
    '3': {'$': (1, 'stavek')},
    '4': {'$': True},
    '5': {'$': (1, 'spremenljivka')},
    '6': {'$': (2, 'branje')},
    '7': {'$': (2, 'pisanje')}
}
```

## Privzeto začetno stanje

Parser privzeto začne analizo v stanju `'0'`.
To lahko spremenimo z argumentom `start` pri
ustvarjanju parserja:

```python
parser = Parser(navodila, start='zacetek')
```

## Posebni primeri

### Ignoriranje terminalov

Če navodila pod ključem `''` vsebujejo seznam
imen terminalov, bo parser te terminale prezrl,
kadar se nepričakovano pojavijo (namesto da bi
sprožil napako).

```python
navodila = {
    '': ['PRESLEDEK', 'KOMENTAR'],  # Ignoriramo, če se pojavijo nepričakovano.
    '0': {...},
    ...
}
```

### Privzeta akcija (prazen ključ v stanju)

Če stanje vsebuje prazen ključ `''`, se ta
akcija izvede, kadar naletimo na terminal, ki
ni eksplicitno naveden. To omogoča pisanje bolj
kompaktnih navodil.

```python
'3': {
    '$': (1, 'stavek'),
    '': '5'  # Za vse ostale terminale pojdi v stanje 5.
}
```

### Pomožni neterminali

Pomožni neterminali imajo ime, ki se začne s
podčrtajem in malo začetnico (npr. `_seznam`).
Njihova posebnost je, da se v končnem drevesu
**ne pojavijo kot samostojno vozlišče** —
namesto tega se njihovi otroci prenesejo
neposredno v nadrejeno vozlišče.

To je uporabno za ponavljajoče se vzorce
(npr. sezname), kjer vmesna vozlišča niso
zaželena.

Primer: če imamo slovnico za seznam imen ...

```
seznam: IME _rep
_rep: "," IME _rep
   |
```

... bo ob vhodu `a, b, c` nastalo drevo:

```
seznam:
  IME a
  IME b
  IME c
```

in ne globlje gnezdeno:

```
seznam:
  IME a
  _rep:
    IME b
    _rep:
      IME c
```

### Lažni terminali

Lažni terminali imajo ime iz velikih črk, ki pa
se konča s podčrtajem (npr. `VREDNOST_`).
Kljub temu, da so definirani s pravilom
predelave (REDUCE) — torej so formalno
neterminali — se ob gradnji drevesa obnašajo
kot terminali: vsi njihovi otroci se **združijo
v en sam žeton**, katerega vrednost je
združena vrednosti vseh podrejenih terminalov.

To je uporabno, kadar želimo iz več žetonov
sestaviti enega samega. Primer: če imamo
pravilo za sestavljeno vrednost ...

```
_VREDNOST: IME "=" IME
```

... bo ob vhodu `a = b` nastal žeton
`Token(name='_VREDNOST', value='ab')` namesto
drevesa s podrejenimi vozlišči.

### Pomožni terminali

Med predelavo (REDUCE) parser samodejno odstrani
terminale, katerih ime se začne z `"`, `'`, `/` ali `_`.
To so nepoimenovani, nepoimenovani terminali (npr.
`"beri"`, `"="`) ali poimenovani terminali, katerih ime
se začne s `_` (npr. `_TERMINAL`). Ti terminali služijo
le za prepoznavanje vzorca in v končnem drevesu niso
potrebni.

## Obravnava napak

Ob nepričakovanem terminalu se sproži `SyntaxError`
z informativnim sporočilom, ki vključuje:

* pričakovane terminale za trenutno stanje,
* vrstico in stolpec, kjer se je napaka zgodila,
* izpis problematične vrstice s puščico (`^`).

## Primer uporabe

```python
from boho.parser import Parser
from boho.objects import Token

navodila = {
    '0': {'"beri"': '1',
          '"piši"': '2',
          'branje': '3',
          'pisanje': '3',
          'stavek': '4'},
    '1': {'IME': '5', 'spremenljivka': '6'},
    '2': {'IME': '5', 'spremenljivka': '7'},
    '3': {'$': (1, 'stavek')},
    '4': {'$': True},
    '5': {'$': (1, 'spremenljivka')},
    '6': {'$': (2, 'branje')},
    '7': {'$': (2, 'pisanje')}
}

zetoni = [
    Token('"beri"', 'beri'),
    Token('IME', 'x'),
]

parser = Parser(navodila)
drevo = parser(zetoni)

print(drevo.pretty())
# stavek:
#   branje:
#     spremenljivka:
#       IME x
```
