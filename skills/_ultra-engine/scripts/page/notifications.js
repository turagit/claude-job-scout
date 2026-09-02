// notifications.js — run on https://www.linkedin.com/notifications/?filter=jobs_all
// Exhausts "Load more", returns every job-alert link. Anchors: evidence §1 only.
const sleep = ms => new Promise(r => setTimeout(r, ms));
const loadMore = () => [...document.querySelectorAll('button')].find(b => b.innerText.trim() === 'Load more');
let clicks = 0;
for (let i = 0; i < 25; i++) { const b = loadMore(); if (!b) break; b.click(); clicks++; await sleep(1500); }
window.scrollTo(0, document.body.scrollHeight); await sleep(800);
const seen = new Set(); const alerts = [];
for (const a of document.querySelectorAll('a[href*="alertAction=viewjobs"]')) {
  if (seen.has(a.href)) continue; seen.add(a.href);
  let n = a, age = '';
  for (let i = 0; i < 6 && n; i++) {
    n = n.parentElement; if (!n) break;
    const t = (n.innerText || '').split('\n').map(s => s.trim()).find(s => /^\d+\s?(m|h|d|w|min|mins|hr|hrs|hour|hours|day|days|week|weeks)$/.test(s));
    if (t) { age = t; break; }
  }
  alerts.push({ href: a.href, age_text: age });
}
const out = { surface: 'notifications', url: location.href, load_more_clicks: clicks, exhausted: !loadMore(), alerts };
JSON.stringify(out)
