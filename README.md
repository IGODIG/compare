# Magnet — sticle compatibile

Instrument web pentru ateliere de reparații telefoane. Caută un model și vezi telefoane care pot folosi aceeași sticlă, potriviri probabile și recomandarea de protecție pentru ecrane curbate sau pliabile.

Site-ul este static și se publică prin GitHub Pages: [igodig.github.io/compare](https://igodig.github.io/compare/). `index.html` este un shell mic; codul, catalogul și imaginile sunt fișiere separate. Catalogul se încarcă la pornire, sursele la deschiderea fișei, iar imaginile pe măsură ce intră în ecran. Fontul Manrope este găzduit local, iar GitHub Actions limitează fotografiile individuale la 600 KB.

## Cum se calculează potrivirile

- **Confirmat după dimensiuni:** corpul diferă cu maximum ±0,5 mm la lungime și lățime, ambele ecrane sunt plate și au aceeași categorie de decupaj frontal: cameră pe ecran sau picătură.
- **Probabil:** diagonala diferă cu maximum 0,1″, lungimea corpului cu maximum 2 mm și lățimea cu maximum 1 mm; camera trebuie să fie de același tip. Sticla trebuie probată fizic.
- **Curbat sau pliabil:** site-ul recomandă folie hydrogel. La modelele pliabile, folia interioară trebuie verificată după recomandarea producătorului.
- Perechile confirmate din surse și testele salvate se păstrează separat. Voturile de probă se salvează în browserul local.
- Rezultatele prioritizează Samsung, apoi Xiaomi; în fiecare grup, modelele apropiate după dimensiuni apar primele.
- Candidatele afișează diferența de lungime și lățime și forma decupajului camerei față de modelul căutat. Favoritele și modelele deschise recent se salvează local în browser.

Detalii: [Regulile de compatibilitate](docs/COMPATIBILITY.md).

## Structura repository-ului

```text
.
├── index.html                      # Shell rapid pentru GitHub Pages
├── app.js                          # Interfața aplicației
├── matching.mjs                    # Reguli de potrivire, folosite și în teste
├── styles.css                      # Stilurile site-ului
├── data.json                       # Modele cu ID-uri stabile și relații
├── favicon.svg
├── data/
│   ├── compatibility-evidence.json # Dovezi încărcate la deschiderea unei fișe
│   ├── image-fallbacks.json        # Imagini alternative indexate după ID
│   ├── model-codes.json             # Coduri de model căutabile, de ex. SM-G988B
│   ├── phone-images.json           # Imagini frontale locale și sursele lor
│   └── new-model-candidates.json   # Candidați încă neverificați
├── assets/
│   ├── fonts/                      # Manrope local (OFL)
│   ├── image-bundles/              # Pachete de imagini încărcate la cerere
│   └── phones/                     # Fotografii locale
├── docs/COMPATIBILITY.md
├── scripts/
│   ├── audit_critical_images.py
│   ├── check_image_budget.py
│   ├── audit_model_completeness.py
│   ├── build_standalone.py         # Generează index-complet.html la cerere
│   ├── discover_new_models.py
│   ├── discover_official_models.py
│   └── validate_project.py
├── tests/matching.test.mjs         # Regresii pentru reguli și ordinea rezultatelor
└── .github/workflows/
    ├── audit-images.yml
    ├── discover-models.yml
    └── validate.yml
```

Modelele se leagă între ele prin ID-uri stabile, nu prin poziția rândului în listă. Astfel, inserarea sau reordonarea modelelor nu mută perechile compatibile și mapările imaginilor.

## Dezvoltare și verificare

Pornește un server local din rădăcina repository-ului:

```bash
python -m http.server 8000
```

Accesează `http://localhost:8000`. Verificările proiectului:

```bash
python scripts/validate_project.py
python scripts/check_image_budget.py
node --test tests/matching.test.mjs
python scripts/build_standalone.py
```

Pentru o copie HTML autonomă, rulează `python scripts/build_standalone.py`. Aceasta generează `index-complet.html`; fișierul principal pentru GitHub Pages rămâne modular și mic.

## Actualizare și publicare

Adaugă modelul verificat în `data.json` cu un ID stabil nou (`m_` și 12 cifre hexazecimale). Relațiile din câmpurile `10`, `13` și grupele `g` folosesc ID-uri stabile. Înregistrează în `data/phone-images.json` numai imagini cu telefonul văzut din față; redimensionează-le pentru interfață și păstrează fișierele locale sub 600 KB. Decupajele pentru fotografiile compozite se salvează în `assets/phones/front/`. GitHub Actions verifică dimensiunea imaginilor, iar GitHub Pages servește direct fișierele statice.

Scanarea lunară compară sursele oficiale și GSMArena și deschide un pull request cu modele-candidat. Candidații nu apar pe site înainte de verificarea dimensiunilor, pieței, camerei și fotografiei. Auditul săptămânal verifică imaginile Oppo și OnePlus Global.

Pentru ca workflow-ul să deschidă pull request-uri, repository-ul trebuie să permită GitHub Actions să creeze pull request-uri în **Settings → Actions → General**.

Mai multe instrucțiuni: [CONTRIBUTING.md](CONTRIBUTING.md) și [ghidul de contribuție](CONTRIBUTING.md).
