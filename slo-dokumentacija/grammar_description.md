# Metajezik boho

Metajezik boho služi za opis slovnice in terminalov, na podlagi katerega se avtomatsko zgenerirajo navodila za
leksikalno in sintaktično analizo.

## Komentarji

Komentarji so enako kot v C-ju: `// ...` do konca vrstice ali `/* ... */` čez več vrstic.

## Opis terminalov

Terminale opišemo na tri načine:

- **Niz znakov** — točno določeno zaporedje (npr. `"if"`, `'='`).
- **Regularni izraz** — med poševnicama (npr. `/\d+/`).
- **Vnaprej pripravljen opis** — z `@` in imenom (npr. `@NIZ`, `@INT`, `@FLOAT`).

Te opise lahko uporabimo neposredno v slovničnih pravilih kot *nepoimenovane terminale*, ki se izrežejo iz sintaktičnega
drevesa.

Za ohranitev v drevesu moramo terminal *poimenovati* (ime z velikimi črkami):

```
PLUS: "+"               // Niz
NARAVNO_STEVILO: /\d+/  // Regularni izraz
CELO_STEVILO: @INT      // Vnaprej pripravljen opis
```

Če se ime začne s podčrtajem (npr. `_DOLG_KOMENTAR`), se terminal kljub poimenovanju izreže iz drevesa.

## Slovnična pravila

Neterminal opišemo z `neterminal: opis` (ime z malimi črkami). Možnosti ločimo z `|`:

```
spremenljivka: IME "=" vrednost
vrednost: IME | STEVILO
```

Podprte so EBNF-razširitve:

```
besedilo: odstavek+             // + = ena ali več ponovitev
odstavek: poved* "\n"           // * = nič ali več ponovitev
poved: stavek (veznik stavek)*  // oklepaji za grupiranje
navaden: osebek? povedek        // ? = neobvezno
```

Z oznako `->` lahko inline poimenujemo posamezne možnosti:

```
stavek: osebek? povedek predmet? -> navaden
      | MEDMET+                  -> pastavek
```

### Lažni terminali

Lažni terminali (ime z velikimi črkami, ki se konča s podčrtajem, npr. `KOMENTAR_`) se opišejo kot neterminali, a se pri
analizi preoblikujejo v en sam žeton. Omogočajo prepoznavanje struktur, ki jih regularni izrazi ne morejo opisati (npr.
gnezdeni komentarji).

## Preklapljanje med načini leksanja

Po zgledu orodja ANTLR podpiramo modalni lekser. Za terminalom lahko z `->` navedemo operacije na skladu načinov:

| Zapis       | Učinek               |
|-------------|----------------------|
| (brez)      | brez spremembe       |
| `-> +nacin` | dodaj način na sklad |
| `-> -`      | odstrani vrh sklada  |
| `-> nacin`  | zamenjaj vrh sklada  |
| `-> -2`     | odstrani 2 načina    |
| `-> --`     | izprazni sklad       |

Načine določimo z `#ime_nacina` v samostojni vrstici. Terminali pred prvim `#`-stavkom pripadajo vsem načinom. Primer:

```
OKLEPAJ: "(" -> +stevilo
ZAKLEPAJ: ")" -> -

#besedilo
BESEDA: /[^(]+/

#stevilo
CELO: /-?\d+/ -> operacija
```

## Ignoriranje

S stavkom `%ignore TERMINAL` parserju povemo, katere žetone naj ignorira (tipično presledki, komentarji). Če ignoriramo
niz z enim samim znakom, ga ignorira že lekser — zato je pri modalnem lekserju pomembno, kje (pred ali za `#`-stavkom)
se `%ignore` pojavi.

## Opis jezika boho v jeziku boho

```
START: "/*" -> +komentar

#boho

start: _stavek+

_stavek: _NV
       | V_IME ":" opis operacije? -> terminal
       | _ime ":" moznosti         -> nonterminal
       | "#" M_IME                 -> nacin
       | "%ignore" (opis | V_IME)  -> ignoriranje
       | _DOLG_KOMENTAR_

opis: NIZ
    | REGEX
    | AFNA
operacije: "->" _operacija+
_operacija: P M_IME -> dodajanje
          | "-" N?  -> brisanje
          | "--"    -> izpraznitev
          | M_IME   -> menjava

_ime: M_IME | L_IME
moznosti: moznost (_ALI moznost)*
moznost: enote ("->" _ime)?
enote: enota+
enota: atom oznaka?
atom: V_IME | _ime | opis
    | "(" moznosti ")"
oznaka: V | Z | P

V: "?"
Z: "*"
P: "+"

M_IME: /_?[a-z][a-z_]*/
L_IME: /_?[A-Z][A-Z_]*_/
V_IME: /[A-Z_]*[A-Z]/

NIZ: @NIZ
REGEX: /\/([^\/*]|\\\/|\\\*)([^\/]|\\\/)*\//
AFNA: /@[A-Z_]*/
N: /\d+/

_ALI: /(\n\s*)?\|\s*/
_NV: /\n\s*/


%ignore " "
%ignore /\/\/([^\n]*[^\/])?/

#komentar

_DOLG_KOMENTAR_: START _vsebina* STOP
_vsebina: VSEBINA | _DOLG_KOMENTAR_
VSEBINA: /([^*\/])+|\\*|\//
STOP: "*/" -> -
```