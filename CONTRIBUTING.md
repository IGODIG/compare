# Ghid de contribuție

## Adăugarea unui model

Înainte să apară în site, înregistrează și verifică:

- numele și varianta Global/Europa;
- diagonala și dimensiunile corpului în milimetri;
- tipul decupajului frontal și dacă ecranul este plat sau curbat;
- fotografia modelului și sursa ei;
- detaliile ecranului activ, dacă sunt disponibile.

Modelele doar anunțate, variantele exclusiv China și informațiile incomplete nu trebuie prezentate drept potriviri confirmate.

## Sincronizarea datelor

Pagina folosește o copie încorporată a `data.json`. După editarea JSON-ului, sincronizează și verifică:

```bash
python scripts/sync_embedded_data.py
python scripts/validate_project.py
```

Fotografiile sunt încorporate în `index.html`. Nu schimba `m[7]` către o fotografie care nu există în setul încorporat.

## Modele descoperite automat

Workflow-ul zilnic compară catalogul recent GSMArena cu modelele existente și pune rezultatele noi în `data/new-model-candidates.json`. Pull request-ul automat este doar o coadă de verificare. Completează sursele și toate câmpurile înainte să copiezi modelul în `data.json`.

## Înainte de commit

- `python scripts/validate_project.py` trece;
- `data.json` și copia încorporată din `index.html` sunt identice;
- pagina se deschide local și căutarea funcționează;
- imaginile noi se încarcă;
- mesajele „Confirmat” și „Probabil” reflectă corect datele disponibile.
