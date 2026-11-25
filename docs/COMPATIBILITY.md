# Reguli de compatibilitate

## Potrivire confirmată după dimensiuni

Site-ul tratează două modele ca având aceeași sticlă dacă:

1. fiecare dimensiune a corpului — lungime și lățime — diferă cu cel mult 0,5 mm;
2. ambele au același tip de decupaj frontal: cameră pe ecran sau picătură;
3. ambele sunt marcate cu ecran plat.

> Perechile marcate astfel sunt confirmate de regula Magnet, nu de o probă fizică. Confirmările din surse și testele făcute în magazin rămân identificabile separat.

## Potriviri probabile

Candidatele din categoria probabilă folosesc pragurile mai largi existente: diagonală în limita a 0,1″, lungime în limita a 2 mm și lățime în limita a 1 mm, cu decupaj frontal potrivit și fără conflict cunoscut de curbură. Acestea trebuie probate fizic înainte de vânzare.

La căutare, textul introdus determină modelul de referință; apoi sunt prioritizate mărcile Samsung, Xiaomi și celelalte mărci, iar în fiecare grup apar mai întâi dimensiunile cele mai apropiate.

## Hydrogel

Pentru ecranele curbate, aplicația recomandă folie hydrogel, deoarece sticla plată poate lăsa margini neacoperite. Pentru Fold/Flip, interiorul și exteriorul sunt ecrane separate; folia interioară trebuie să respecte instrucțiunile producătorului.

## Câmpuri în `data.json`

Înregistrarea unui model este o listă compactă. Câmpurile folosite de potrivire sunt:

| Index | Câmp |
| --- | --- |
| `0` | Marcă |
| `1` | Model |
| `2` | An |
| `3` | Diagonală |
| `4` | Lungimea corpului, mm |
| `5` | Lățimea corpului, mm |
| `6` | Decupaj frontal |
| `7` | Indexul imaginii încorporate |
| `10` | Perechi confirmate/probabile din surse |
| `14` | Piață |
| `16` | Curbură ecran (`plat`/`curbat`) |

Înregistrările pliabile de tip film folosesc și câmpurile `17` (tipul înregistrării) și `18` (ecran interior/exterior).
