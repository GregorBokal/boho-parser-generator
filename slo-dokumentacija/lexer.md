# Lekser

---

## Opis

Naloga lekserja je razčleniti **_besedilo_**
na **_žetone_** (kar dela na podlagi danih
**_navodil_** za končni avtomat).

## Priprava navodil

Navodila za lekser morajo biti podana kot
slovar, urejen po sledeči strukturi:

```dockerfile
// Izhodiščni slovar
navodila: '{' elementi '}'
elementi: (privzeto | nacin) (',' nacin)*

// Navedba privzetega načina
privzeto: "''" ':' @STR

// Opis konkretnega načina
nacin: @STR ':' koncni_avtomat

koncni_avtomat: '{' (ignoriraj | stanje) (',' stanje)* '}'

// Seznam znakov, ki se lahko pojavljajo med žetoni.
ignoriraj: "''" ':' '[' @STR (',' @STR)* ']'

stanje: @STR ':' '{' moznost (',' moznost)* '}'

moznost: opis_znaka ':' akcija

opis_znaka: @STR // opis z regularnim izrazom
          | "''" // privzeta možnost
          
akcija: @STR // Dopolnjevanje žetona (indeks naslednjega stanja)
      | '[' ime_zetona operacije?']' // zaključek žetona
      
ime_zetona: @STR

operacije: (',' operacija) // Spremembe na skladu načinov

operacija: @STR // Dodajanje načina na vrh sklada
         | '0'  // Izpraznitev sklada
         | /d+/ // Izbris načinov z vrha sklada.
```

Še po slovensko:

* **_Izhodiščni slovar_** ima za ključe
  imena načinov (lekser namreč
  omogoča preklapljanje med različnimi
  načini leksanja), vrednosti pa
  predstavljajo navodila za **_končni avtomat_**
  konkretnega načina.
* **_končni avtomat_** je opisan s slovarjem
  **_stanj_** in morebitno navedbo žetonov, ki  
  se jih pri tem načinu ignorira, če se
  nepričakovano pojavijo med žetoni.
* **_stanje_** je slovar, kjer je pričakovanim
  znakom (ki so lahko opisani z regularnim
  izrazom ali s praznim nizom, ki pomeni
  privzeto možnost) pripisana
  **_akcija_**, ki se ob tem izvede.
* **_akcija_** je lahko:
    * `str`= dopolnjevanje žetona; z nizom
      navedemo ime stanja, v katerem naj se
      analiza nadaljuje (npr. `'1'`, `'2'`)
    * `list` = zaključevanje žetona;
        * prvi element (tipa `str`) predstavlja ime
          žetona.
        * preostali elementi predstavljajo **operacijo
          na skladu načinov**, ki se ob zaključku
          žetona izvede. Ta je lahko:
            * `str`= na vrh sklada dodamo nov način.
            * `0` = sklad izpraznimo.
            * `int`(> 0) = z vrha sklada odstranimo
              določeno število načinov.

### Preprost primer navodil

```python
navodila = {
    '': {  # Edini način leksanja
        '': [' '],  # Ignoriramo presledek
        '0': {  # Začetno stanje (0).
            'h': '1'  # Če vidimo h, gremo v stanje 1.
        },
        '1': {  # Stanje 1
            '[aeiou]': '1',  # Ob aeiou ostanemo v 1.
            '': ['ha']  # Sicer zaključimo žeton 'ha'.
        }
    }
}
```

### Primer naprednejših navodil

```python
navodila = {
    '': 'besedilni_nacin',  # Privzeti način
    'besedilni_nacin': {
        '0': {
            '[^(]': '1',
            r'\(': '2'
        },
        '1': {
            '[^(]': '1',
            '': ['besedilo']
        },
        '2': {
            # Zaključimo '(' in na sklad dodamo nov način.
            '': ['(', 'stevilski_nacin']
        }
    },
    'stevilski_nacin': {
        # V tem načinu ignoriramo presledke
        '': [' '],
        '0': {
            r'\d': '1',
            r'\(': '2',
            r'\)': '3'
        },
        '1': {
            r'\d': '1',
            '': ['stevilo']
        },
        '2': {
            '': ['(', 'stevilski_nacin']
        },
        '3': {
            # Zaključimo ')' in izbrišemo vrhnji način s sklada.
            '': [')', 1]
        }
    }
}
```

## Privzeti začetni način

Lekser določi začetni način na enega od treh načinov
(po prioriteti):

1. Podamo ga kot argument `start_mode` pri ustvarjanju
   lekserja: `Lexer(navodila, start_mode='ime')`.
2. V navodilih navedemo privzeti način pod ključem
   `''`: `{'': 'ime_nacina', ...}`.
3. Uporabi se prvi način v slovarju navodil.

## Obravnava napak

Lekser ob nepričakovanem znaku sproži `SyntaxError`
z informativnim sporočilom, ki vključuje:

* pričakovane znake za trenutno stanje,
* vrstico in stolpec, kjer se je napaka zgodila,
* izpis problematične vrstice s puščico (`^`).

Če ob koncu vhoda žeton ni zaključen, lekser
preveri, ali trenutno stanje vsebuje privzeto
možnost (`''`), ki zaključi žeton. Če ta ne
obstaja, sproži `SyntaxError` z opisom
nedokončanega žetona.

## Primer uporabe

```python
from boho.lexer import Lexer

navodila = {
    '': 'besedilni_nacin',
    'besedilni_nacin': {
        '0': {'[^(]': '1', r'\(': '2'},
        '1': {'[^(]': '1', '': ['besedilo']},
        '2': {'': ['(', 'stevilski_nacin']}
    },
    'stevilski_nacin': {
        '': [' '],
        '0': {r'\d': '1', r'\(': '2', r'\)': '3'},
        '1': {r'\d': '1', '': ['stevilo']},
        '2': {'': ['(', 'stevilski_nacin']},
        '3': {'': [')', 1]}
    }
}

besedilo = '123 je besedilo, (123) pa število.'

lekser = Lexer(navodila)
print(lekser(besedilo))
# [Token(name='besedilo', value='123 je besedilo, ', line=0, col=0),
#  Token(name='(', value='(', line=0, col=18),
#  Token(name='stevilo', value='123', line=0, col=19),
#  Token(name=')', value=')', line=0, col=22),
#  Token(name='besedilo', value=' pa število.', line=0, col=23)]
```
