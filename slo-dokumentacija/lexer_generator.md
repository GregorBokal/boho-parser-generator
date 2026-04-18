# Lekser-generator

---

## Opis

Lekser-generator na podlagi opisov
terminalov zgenerira slovar navodil
za leksikalno analizo (struktura
navodil je opisana v dokumentaciji lekserja).

## Vhodni podatki

Kot vhod je treba za vsak leksikalni način
podati seznam parov `(opis, akcija)`, kjer
je:

- `akcija` (tipa `list`) enaka akciji, ki
  se izvede, ko lekser prepozna žeton (glej
  dokumentacijo lekserja)
- `opis` (tipa `str`) vrednost, na podlagi
  katere se najprej zgenerira končni avtomat
  za prepoznavo le tega žetona. Tak opis je
  lahko podan kot:
    - **Niz znakov** znotraj dvojnih narekovajev, npr. `'"ABC"'`.
    - **Regularni izraz** znotraj dveh poševnic, npr `'/A[BC]/'`.
    - **Ime** vnaprej pripravljenega opisa, ki sledi zanku @, npr `'@INT'`.

## Prednost pri konfliktih

Kadar lahko dva opisa žetona ujameta isti vhod (npr.
ključna beseda `if` ustreza tudi vzorcu za identifikator
`/[a-z]+/`), **zmaga tisti žeton, ki je na seznamu
deklariran prvi**. Z vrstnim redom opisov lahko tako
sami določate prednost — bolj specifične žetone (na
primer ključne besede) postavite pred bolj splošne, če
želite, da so prepoznani posebej, ali pa se zanesete na
pravilo »prvi zmaga«, ki prekrivanja samodejno razreši.

## Primer uporabe

```python
from boho.lexer_generator import generate

tokens = {
    'mode_1': [
        ('"AB"', ['AB', 1, 'mode_1']),
        ('"ABC"', ['ABC'])
    ],
    'mode_2': [
        ('@INT', ['INT']),
        (r'/-?\d*\.\d+/', ['FLOAT', 1, 'mode_2'])
    ]
}

generate(tokens, log=True)

```
