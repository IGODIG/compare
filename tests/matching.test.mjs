import test from 'node:test';
import assert from 'node:assert/strict';
import {
  sameGlassByDimensions,
  physicalMatch,
  strictProbableMatch,
  sortCandidates,
  modelCodeScore,
} from '../matching.mjs';

function phone(brand, overrides = {}) {
  const model = [brand, 'Test model', 2025, 6.5, 150, 70, 'Pe ecran', -1,
    null, null, [], '2026-11-27', null, null, 'Global', null, 'plat'];
  return Object.assign(model, overrides);
}

test('same-glass rule accepts up to 0.5 mm in both body dimensions', () => {
  const base = phone('Samsung');
  assert.equal(sameGlassByDimensions(base, phone('Xiaomi', { 4: 150.5, 5: 69.5 })), true);
  assert.equal(sameGlassByDimensions(base, phone('Xiaomi', { 4: 150.5001 })), false);
});

test('same-glass rule requires matching cutout and flat screens', () => {
  const base = phone('Samsung');
  assert.equal(sameGlassByDimensions(base, phone('Samsung', { 6: 'Picătură' })), false);
  assert.equal(sameGlassByDimensions(base, phone('Samsung', { 16: 'curbat' })), false);
  assert.equal(sameGlassByDimensions(base, phone('Samsung', { 6: 'Necunoscută' })), false);
});

test('probable rule applies the requested inclusive diagonal, length and width limits', () => {
  const base = phone('Samsung');
  assert.equal(physicalMatch(base, phone('Samsung', { 3: 6.6, 4: 152, 5: 71 })), true);
  assert.equal(strictProbableMatch(base, phone('Samsung', { 3: 6.6, 4: 152, 5: 71 })), true);
  assert.equal(physicalMatch(base, phone('Samsung', { 4: 152.001 })), false);
  assert.equal(physicalMatch(base, phone('Samsung', { 5: 71.001 })), false);
  assert.equal(physicalMatch(base, phone('Samsung', { 6: 'Picătură' })), false);
});

test('curvature conflict blocks a probable match when both values are known', () => {
  assert.equal(physicalMatch(phone('Samsung'), phone('Samsung', { 16: 'curbat' })), false);
  assert.equal(physicalMatch(phone('Samsung', { 16: null }), phone('Samsung')), true);
});

test('candidate ordering prioritizes Samsung, then Xiaomi, then closeness', () => {
  const models = [
    phone('Oppo', { 4: 150.01 }),
    phone('Xiaomi', { 4: 153 }),
    phone('Samsung', { 4: 155 }),
    phone('Samsung', { 4: 150.01 }),
  ];
  const sorted = sortCandidates(models[0], [[1], [2], [3], [0]], models);
  assert.deepEqual(sorted.map(([index]) => index), [3, 2, 1, 0]);
});

test('Samsung model-code search accepts exact and partial codes', () => {
  const codes = ['SM-G988B', 'G988B', 'SM-G988', 'G988'];
  assert.equal(modelCodeScore(codes, ['sm', 'g988b']), 2000);
  assert.ok(modelCodeScore(codes, ['g988']) > 0);
  assert.equal(modelCodeScore(codes, ['a13']), -1);
});
