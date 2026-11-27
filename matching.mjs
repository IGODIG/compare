const inSupportedMarket = phone => phone?.[14] === 'Global' || phone?.[14] === 'Europa';
const isFilm = phone => phone?.[17] === 'film';
const glassCutouts = new Set(['Pe ecran', 'Picătură']);

export function sameGlassByDimensions(a, b) {
  return !!(inSupportedMarket(a) && inSupportedMarket(b) && !isFilm(a) && !isFilm(b)
    && a[16] === 'plat' && b[16] === 'plat'
    && a[4] > 0 && b[4] > 0 && a[5] > 0 && b[5] > 0
    && glassCutouts.has(a[6]) && a[6] === b[6]
    && Math.abs(a[4] - b[4]) <= 0.5 && Math.abs(a[5] - b[5]) <= 0.5);
}

export function physicalMatch(a, b) {
  return !!(inSupportedMarket(a) && inSupportedMarket(b)
    && a[3] > 0 && b[3] > 0 && a[4] > 0 && b[4] > 0 && a[5] > 0 && b[5] > 0
    && a[6] && b[6]
    && Math.abs(a[3] - b[3]) <= 0.1
    && Math.abs(a[4] - b[4]) <= 2
    && Math.abs(a[5] - b[5]) <= 1
    && a[6] === b[6]
    && (!a[16] || !b[16] || a[16] === b[16]));
}

export function strictProbableMatch(a, b) {
  return !!(inSupportedMarket(a) && inSupportedMarket(b)
    && a[3] > 0 && b[3] > 0 && a[4] > 0 && b[4] > 0 && a[5] > 0 && b[5] > 0
    && a[6] && b[6] && a[6] === b[6]
    && Math.abs(a[3] - b[3]) <= 0.1
    && Math.abs(a[4] - b[4]) <= 2
    && Math.abs(a[5] - b[5]) <= 1
    && (!a[16] || !b[16] || a[16] === b[16]));
}

export function sameDimensions(a, b) {
  return Math.abs(a[3] - b[3]) < 0.005
    && Math.abs(a[4] - b[4]) < 0.05
    && Math.abs(a[5] - b[5]) < 0.05;
}

export function brandRank(model, base = null) {
  if (base?.[0] === 'Apple') return model[0] === 'Apple' ? 0 : model[0] === 'Samsung' ? 1 : model[0] === 'Xiaomi' ? 2 : 3;
  if (base?.[0] === 'Samsung') return model[0] === 'Samsung' ? 0 : model[0] === 'Xiaomi' ? 1 : 2;
  if (base?.[0] === 'Xiaomi') return model[0] === 'Xiaomi' ? 0 : model[0] === 'Samsung' ? 1 : 2;
  return model[0] === 'Samsung' ? 0 : model[0] === 'Xiaomi' ? 1 : 2;
}

export function modelDistance(a, b) {
  if (!a || !b || !a[3] || !b[3] || !a[4] || !b[4] || !a[5] || !b[5]) return Number.MAX_SAFE_INTEGER;
  return Math.abs(a[4] - b[4]) * 3 + Math.abs(a[5] - b[5]) * 4
    + Math.abs(a[3] - b[3]) * 24 + (a[6] === b[6] ? 0 : 40)
    + (a[16] && b[16] && a[16] !== b[16] ? 60 : 0);
}

export function sortCandidates(base, items, models) {
  return [...items].sort((x, y) => brandRank(models[x[0]], base) - brandRank(models[y[0]], base)
    || modelDistance(base, models[x[0]]) - modelDistance(base, models[y[0]])
    || models[y[0]][2] - models[x[0]][2]);
}

export function modelCodeScore(codes, tokens) {
  const query = tokens.join('').toLowerCase().replace(/[^a-z0-9]/g, '');
  if (query.length < 4 || !/\d/.test(query)) return -1;
  let best = -1;
  for (const code of codes) {
    const normalized = code.toLowerCase().replace(/[^a-z0-9]/g, '');
    if (normalized === query) best = Math.max(best, 2000);
    else if (normalized.startsWith(query) || query.startsWith(normalized)) best = Math.max(best, 800 + Math.min(query.length, 30));
  }
  return best;
}
