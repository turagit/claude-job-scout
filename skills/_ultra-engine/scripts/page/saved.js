// saved.js — run on https://www.linkedin.com/jobs-tracker/ (the redirect target of /my-items/saved-jobs/)
// Reads the Saved tab count; extracts cards through either known selector set. Anchors: evidence §4.
const sleep = ms => new Promise(r => setTimeout(r, ms));
await sleep(1500);
const savedTab = [...document.querySelectorAll('button,a,[role=tab],span')].find(e => /^Saved\s*·\s*\d+$/.test((e.innerText || e.textContent || '').trim()));
let savedCount = null;
if (savedTab) { savedCount = parseInt((savedTab.innerText || savedTab.textContent).replace(/\D/g, ''), 10); if (savedTab.click && savedTab.getAttribute('aria-selected') !== 'true') { savedTab.click(); await sleep(1500); } }
for (let i = 0; i < 6; i++) { window.scrollTo(0, document.body.scrollHeight); await sleep(600); }
const seen = new Set(); const cards = [];
for (const e of document.querySelectorAll('[componentkey^="job-card-component-ref-"], li[data-occludable-job-id], [data-job-id]')) {
  const id = (e.getAttribute('componentkey') || '').replace('job-card-component-ref-', '') || e.getAttribute('data-occludable-job-id') || e.getAttribute('data-job-id') || '';
  if (!/^\d{6,}$/.test(id) || seen.has(id)) continue; seen.add(id);
  const host = e.closest('li') || e; cards.push({ id, text: host.innerText });
}
if (!cards.length) { for (const a of document.querySelectorAll('a[href*="/jobs/view/"]')) { const m = a.href.match(/\/jobs\/view\/(\d+)/); if (m && !seen.has(m[1])) { seen.add(m[1]); const host = a.closest('li') || a.parentElement; cards.push({ id: m[1], text: host ? host.innerText : a.innerText }); } } }
const out = { surface: 'saved', url: location.href, claimed_results: null, page: 1, cards, divider_index: null, has_next: false, saved_count: savedCount };
JSON.stringify(out)
