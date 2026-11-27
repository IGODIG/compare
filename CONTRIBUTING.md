# Ghid de contribuție

## Adăugarea unui model

Înainte să apară în site, verifică numele și piața Global/Europa, diagonala și dimensiunile corpului, forma decupajului, curbura ecranului, fotografia și sursele.

Fiecare rând din `data.json` are un ID stabil în câmpul `19`, de forma `m_` urmat de 12 caractere hexazecimale. Generează-l o singură dată și păstrează-l la editările viitoare. Relațiile din câmpurile `10` și `13`, grupele `g` și manifestele imaginilor folosesc acest ID, nu poziția telefonului în listă.

Pentru o fotografie locală, salvează fișierul în `assets/phones/` și adaugă o intrare cu ID-ul modelului, numele fișierului și URL-ul sursei în `data/phone-images.json`. Pachetele principale de imagini din `assets/image-bundles/` nu trebuie reordonate sau renumerotate fără actualizarea ID-urilor de imagine din câmpul `7`.

## Verificări

Rulează înainte de commit:

```bash
python scripts/validate_project.py
node --test tests/matching.test.mjs
```

Testele folosesc aceleași funcții din `matching.mjs` ca pagina și verifică pragurile, camera, curbura și ordinea rezultatelor.

Pornește pagina cu un server local (`python -m http.server 8000`), apoi deschide `http://localhost:8000`. Pentru un singur fișier HTML, rulează `python scripts/build_standalone.py`; acesta generează `index-complet.html`.

## Modele descoperite automat

Scanarea lunară compară catalogul GSMArena și sursele oficiale. Pull request-ul automat este doar o coadă de verificare. Candidații nu intră în site până când datele și sursele nu sunt verificate.
