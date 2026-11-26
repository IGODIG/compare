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
│   ├── phone-images.json         # Sursa fiecărei fotografii salvate local
│   └── new-model-candidates.json  # Modele descoperite automat, încă neverificate
├── assets/
│   └── phones/                    # Fotografii locale pentru modele fără imagine încorporată
├── docs/
│   └── COMPATIBILITY.md           # Reguli și explicații pentru întreținere
├── scripts/
│   ├── audit_critical_images.py   # Verifică săptămânal fotografiile Oppo și OnePlus
│   ├── discover_new_models.py     # Caută modele noi pe GSMArena
│   ├── discover_official_models.py # Scanează surse oficiale, după programul brandurilor
│   ├── sync_embedded_data.py      # Copiază data.json în index.html
│   └── validate_project.py        # Verifică datele, fotografiile și sintaxa JavaScript
└── .github/workflows/
    ├── audit-images.yml           # Audit săptămânal, luni la 05:37 UTC
    ├── discover-models.yml         # Scanare lunară și PR pentru candidați
    ├── sync-model-database.yml     # Sincronizează automat data.json în site la push
    └── validate.yml                # Validează datele și JavaScript-ul
```

`index.html` rămâne la rădăcină pentru publicarea directă prin GitHub Pages. Majoritatea fotografiilor sunt încorporate în pagină; imaginile locale din `assets/phones/` acoperă modelele ale căror fotografii nu sunt în setul încorporat. Sursa fiecărei imagini locale este păstrată în `data/phone-images.json`.

## Deschidere locală

Deschide `index.html` direct în browser sau pornește un server local:

```bash
python -m http.server 8000
```

Apoi accesează `http://localhost:8000`.

## Actualizare și publicare

1. Adaugă în `data.json` datele verificate ale modelului și păstrează sursa în câmpul `sources`.
2. Pentru o fotografie locală, salvează fișierul în `assets/phones/` și înregistrează indexul modelului și URL-ul sursei în `data/phone-images.json`.
3. Local, rulează `python scripts/sync_embedded_data.py` și `python scripts/validate_project.py` înainte de commit.
4. La push pe `main`, `sync-model-database.yml` încorporează automat baza și maparea imaginilor în `index.html`, validează rezultatul și face commit la HTML-ul generat.
5. Site-ul recalculează automat potrivirile pentru toate modelele. Nu sunt necesare perechi de compatibilitate introduse manual când dimensiunile și forma camerei sunt completate.

> Toate brandurile sunt scanate lunar din surse oficiale, iar GSMArena este încercată ca sursă suplimentară. Erorile unei surse nu opresc scanarea celorlalte. Scanarea deschide/actualizează un pull request cu modele-candidat, fără să adauge modele neverificate în site. Dimensiunile, piața, decupajul și fotografia trebuie confirmate înainte de publicare.

Auditul săptămânal verifică dacă modelele Oppo și OnePlus marcate Global au imagini valide salvate în repository. Auditul nu verifică automat fotografia vizuală; sursa și fișierul trebuie confirmate la adăugarea unui model nou.

Pentru ca workflow-ul să poată deschide pull request-uri, repository-ul trebuie să permită GitHub Actions să creeze pull request-uri în **Settings → Actions → General**.

Mai multe instrucțiuni: [CONTRIBUTING.md](CONTRIBUTING.md).
