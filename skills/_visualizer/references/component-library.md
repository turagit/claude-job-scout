# Component Library

The HTML class primitives that templates compose. Every primitive is implemented in `../assets/theme.css`. Templates use class names; they do not redefine styles.

## `.report-header`

The hero block at the top of every HTML report. Composed of:

```html
<header class="report-header">
  <div class="icon">★</div>
  <div>
    <h1>{{ data.title }}</h1>
    <div class="subtitle">{{ data.subtitle }}</div>
  </div>
</header>
```

The `★` icon is rendered with the violet→pink gradient. Templates may swap the glyph (e.g., 📬 for inbox); the gradient is preserved by `theme.css`.

## `.job-card` / `.thread-card` / `.event-card`

Three names for the same card primitive — semantic differentiation only. All three share the visual treatment.

```html
<article class="job-card" data-tier="a" data-sort_score="87" data-sort_date="2026-04-29">
  <div class="header">
    <div class="title">Senior Backend Engineer</div>
    <div class="score-pill tier-a">87</div>
  </div>
  <div class="meta">Stripe · Remote · €180–220k</div>
  <div>
    <span class="tag-chip">Go</span>
    <span class="tag-chip">Payments</span>
    <span class="tag-chip accent">Senior IC</span>
  </div>
</article>
```

`data-tier` and `data-sort_*` attributes are read by `interactive.js` for filter/sort. The dispatcher emits them; templates iterate.

## `.score-pill`

Three-variant pill: `tier-a` (gradient), `tier-b` (amber), `tier-c` (gray). Always wraps a numeric score.

## `.tag-chip` / `.tag-chip.accent`

Small pill chip for keywords, skills, signals. Default is violet on `--surface-soft`; `.accent` flips to pink-on-pink for variety.

## `.metric-block`

Used in `funnel-report` for big-number stats:

```html
<div class="metric-block">
  <div class="label">Applications sent</div>
  <div class="value">12</div>
  <div class="delta up">+3 vs last week</div>
</div>
```

`.delta.up` is green; `.delta.down` is red. Templates pass `up` or `down` based on sign.

## `.timeline-item`

Used in `check-inbox` and `interview-prep` for chronological lists. Renders a left-rail dot:

```html
<div class="timeline-item">
  <div class="meta">2026-04-28 · Sarah from Stripe</div>
  <div>"Saw your profile and wanted to chat about a Senior Backend role..."</div>
</div>
```

## `.fold`

Collapsible section with a chevron. Used in `interview-prep` and inside long thread cards.

```html
<div class="fold">
  <div class="fold-header">
    <span>Company background</span>
    <span class="chevron">›</span>
  </div>
  <div class="fold-body">
    <p>Stripe is a payments infrastructure company...</p>
  </div>
</div>
```

JS toggles `.open` on the outer `.fold`. Print stylesheet forces all folds open.

## `.empty-state`

Used when a command produces zero results.

```html
<div class="empty-state">
  <div class="icon">🌱</div>
  <div class="title">No new matches today.</div>
  <div class="hint">Try refining your search filters or running again later.</div>
</div>
```

## `.toolbar`

Horizontal row of sort/filter buttons. Always sits immediately above a list of `.job-card`s (etc.) — `interactive.js` finds the list as `nextElementSibling`.

```html
<div class="toolbar">
  <button data-sort="score" class="active">Score ↓</button>
  <button data-sort="date">Date ↓</button>
  <button data-sort="company">Company A–Z</button>
  <span style="flex:1"></span>
  <button data-filter="all" class="active">All</button>
  <button data-filter="a">A-tier</button>
  <button data-filter="b">B-tier</button>
</div>
```

## `.copy-btn`

Small button that copies a sibling element's text to clipboard. Used in `interview-prep` for prep paragraphs and in any view for cover-letter-shaped output (Tier 2 work; reserved primitive).

```html
<button class="copy-btn" data-copy-target="prep-1">Copy</button>
<div id="prep-1">...prep content...</div>
```

JS handles the click, swaps the label to "Copied!" for 1.5 s.

## Footer

Every report ends with:

```html
<footer>
  Generated 2026-04-29 14:30 · linkedin-job-hunter v0.7.0
</footer>
```

Templates fill the timestamp from `data.generated_at` (always provided by the dispatcher).
