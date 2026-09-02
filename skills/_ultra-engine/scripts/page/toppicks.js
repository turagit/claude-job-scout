// toppicks.js — run on https://www.linkedin.com/jobs/collections/recommended/
// Old (Ember) markup: occludable cards must be scrolled into existence. Anchors: evidence §3 only.
const sleep = ms => new Promise(r => setTimeout(r, ms));
const isScroller = e => { const s = getComputedStyle(e); return /(auto|scroll)/.test(s.overflowY) && e.scrollHeight > e.clientHeight + 100; };
const count = () => document.querySelectorAll('li[data-occludable-job-id]').length;
let pane = null; const first = document.querySelector('li[data-occludable-job-id]');
if (first) { let n = first.parentElement; while (n && !isScroller(n)) n = n.parentElement; pane = n; }
let last = -1;
for (let i = 0; i < 12 && count() !== last; i++) { last = count(); if (pane) pane.scrollTop = pane.scrollHeight; else window.scrollTo(0, document.body.scrollHeight); await sleep(700); }
if (pane) { pane.scrollTop = 0; await sleep(300); }
const cards = [...document.querySelectorAll('li[data-occludable-job-id]')].map(li => {
  const inner = li.querySelector('[data-job-id]');
  return { id: li.getAttribute('data-occludable-job-id') || (inner && inner.getAttribute('data-job-id')) || '', text: li.innerText };
});
const active = [...document.querySelectorAll('button[aria-label^="Page"]')].find(b => { const v = b.getAttribute('aria-current'); return v === 'page' || v === 'true'; });
const page = active ? parseInt(active.innerText.trim(), 10) || 1 : 1;
const hasNext = [...document.querySelectorAll('button[aria-label^="Page"]')].some(b => parseInt(b.innerText.trim(), 10) > page);
const out = { surface: 'toppicks', url: location.href, claimed_results: null, page, cards, divider_index: null, has_next: hasNext, saved_count: null };
JSON.stringify(out)
