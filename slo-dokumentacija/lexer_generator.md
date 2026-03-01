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
