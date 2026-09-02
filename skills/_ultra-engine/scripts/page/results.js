// results.js — run on an alert results page (https://www.linkedin.com/jobs/search-results/?…)
// Returns the page dump for cards_parse.py --surface alert. Anchors: evidence §2 only.
const sleep = ms => new Promise(r => setTimeout(r, ms));
const isScroller = e => { const s = getComputedStyle(e); return /(auto|scroll)/.test(s.overflowY) && e.scrollHeight > e.clientHeight + 100; };
let pane = null;
for (const c of document.querySelectorAll('[componentkey^="job-card-component-ref-"]')) {
  let n = c.parentElement; while (n && !isScroller(n)) n = n.parentElement; if (n) { pane = n; break; }
}
if (pane) { for (let i = 0; i < 6; i++) { pane.scrollTop = pane.scrollHeight; await sleep(500); } pane.scrollTop = 0; await sleep(300); }
const all = [...document.querySelectorAll('[componentkey^="job-card-component-ref-"]')];
const outer = all.filter(c => !(c.parentElement && c.parentElement.closest('[componentkey^="job-card-component-ref-"]')));
const divider = [...document.querySelectorAll('p,span,div')].find(e => e.children.length === 0 && /^We found more results related to your search/.test(e.textContent.trim()));
let dividerIndex = null;
if (divider) { dividerIndex = 0; for (const c of outer) { if (c.compareDocumentPosition(divider) & Node.DOCUMENT_POSITION_FOLLOWING) dividerIndex++; } }
const cards = outer.map(c => ({ id: c.getAttribute('componentkey').replace('job-card-component-ref-', ''), text: c.innerText }));
const claimedEl = [...document.querySelectorAll('p,span,div,h1,h2')].find(e => e.children.length === 0 && /^\d[\d,]*\+?\s+results?$/.test(e.textContent.trim()));
const active = document.querySelector('[data-testid="pagination-controls-list"] button[aria-current="true"]');
const page = active ? parseInt(active.innerText.trim(), 10) || 1 : 1;
const hasNext = !!document.querySelector('button[data-testid="pagination-controls-next-button-visible"]');
const out = { surface: 'alert', url: location.href, claimed_results: claimedEl ? claimedEl.textContent.trim() : null, page,
              cards, divider_index: dividerIndex, has_next: hasNext, saved_count: null };
JSON.stringify(out)
