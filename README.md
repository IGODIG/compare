# Magnet — sticle compatibile

Instrument web pentru ateliere de reparații telefoane. Caută un model și vezi telefoane care pot folosi aceeași sticlă, potriviri probabile și recomandarea de protecție pentru ecrane curbate sau pliabile.

Site-ul este static și se publică prin GitHub Pages: [igodig.github.io/compare](https://igodig.github.io/compare/). Nu are nevoie de server, bază de date sau proces de build.

## Cum se calculează potrivirile

- **Confirmat după dimensiuni:** corpul diferă cu maximum ±0,5 mm la lungime și lățime, ambele ecrane sunt plate și au aceeași categorie de decupaj frontal: cameră pe ecran sau picătură.
- **Probabil:** dimensiunile și forma sunt apropiate, dar nu trec regula strictă. Sticla trebuie probată fizic.
- **Curbat sau pliabil:** site-ul recomandă folie hydrogel. La modelele pliabile, folia interioară trebuie verificată după recomandarea producătorului.
- Perechile confirmate din surse și testele salvate se păstrează separat în date. Voturile de probă se salvează în browserul local.
- Rezultatele din căutare prioritizează Samsung, apoi Xiaomi; în fiecare grup, modelele apropiate după dimensiuni apar primele.

Detalii și praguri: [Regulile de compatibilitate](docs/COMPATIBILITY.md).

## Structura repository-ului

```text
.
├── index.html                     # Site-ul static, inclusiv datele și imaginile încorporate
├── data.json                      # Datele sursă despre modele și compatibilități
├── favicon.svg                    # Iconul site-ului
├── data/
│   └── new-model-candidates.json  # Modele descoperite automat, încă neverificate
├── docs/
│   └── COMPATIBILITY.md           # Reguli și explicații pentru întreținere
├── scripts/
│   ├── discover_new_models.py     # Caută zilnic modele noi pe GSMArena
│   ├── sync_embedded_data.py      # Copiază data.json în index.html
│   └── validate_project.py       # Verifică datele și sintaxa JavaScript
└── .github/workflows/             # Verificări și scanarea zilnică
```

`index.html` rămâne la rădăcină pentru publicarea directă prin GitHub Pages. Datele și fotografiile sunt încorporate pentru ca pagina să funcționeze fără dependențe de fișiere locale.

## Deschidere locală

Deschide `index.html` direct în browser sau pornește un server local:

```bash
python -m http.server 8000
```

Apoi accesează `http://localhost:8000`.

## Actualizare și publicare

1. Editează `data.json` și completează datele verificate ale modelului.
2. Dacă ai adăugat fotografii, actualizează și setul de imagini încorporate în `index.html`.
3. Rulează `python scripts/sync_embedded_data.py` și `python scripts/validate_project.py`.
4. Deschide site-ul local, verifică o căutare și commită `data.json` împreună cu `index.html`.
5. Publicarea se face la push pe branch-ul `main`.

> Scanarea zilnică găsește modele-candidat și deschide/actualizează un pull request. Nu adaugă automat modele neverificate în site: dimensiunile, piața, decupajul și fotografia trebuie confirmate înainte de publicare.

Pentru ca workflow-ul să poată deschide pull request-uri, repository-ul trebuie să permită GitHub Actions să creeze pull request-uri în **Settings → Actions → General**.

Mai multe instrucțiuni: [CONTRIBUTING.md](CONTRIBUTING.md).
