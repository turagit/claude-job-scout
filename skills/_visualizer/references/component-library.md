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
<article class="job-card" data-tier="A" data-sort_date="2026-06-09" data-sort_company="Stripe">
  <div class="header">
    <div class="title">Senior Backend Engineer <span class="tag-chip" style="background:var(--accent-from);color:#fff">⚡ apply early</span></div>
    <div class="score-pill tier-a">A</div>
  </div>
  <div class="meta">Stripe · Remote · €180–220k · 2026-06-09 · 12 applicants</div>
  <div>
    <span class="tag-chip">Go</span>
    <span class="tag-chip">Payments</span>
    <span class="tag-chip accent">Senior IC</span>
  </div>
</article>
```

`data-tier` carries the uppercase rubric tier (`A|B|C|D`); `data-sort_*` attributes are read by `interactive.js` for filter/sort. The dispatcher emits them; templates iterate. The "⚡ apply early" chip renders when the payload entry has `fresh: true` (A/B-tier, posted within 48 hours — see `shared-references/linkedin-search.md` §6).

## `.score-pill`

Four-variant pill: `tier-a` (gradient), `tier-b` (amber), `tier-c` (grey), `tier-d` (muted). Wraps the **tier letter** — the CSS class takes the lowercased tier (`tier-{{ job.tier|lower }}`).

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
  <button data-sort="date" class="active">Date ↓</button>
  <button data-sort="company">Company A–Z</button>
  <span style="flex:1"></span>
  <button data-filter="all" data-filter-attr="tier" class="active">All</button>
  <button data-filter="A" data-filter-attr="tier">A-tier</button>
  <button data-filter="B" data-filter-attr="tier">B-tier</button>
  <button data-filter="D" data-filter-attr="tier">Filtered</button>
</div>
```

Filter values match the card's `data-tier` casing exactly (uppercase tiers).

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

## `.job-card` v1 — dimension breakdown (v0.8.0+)

The job-card primitive now carries an optional `dimensions` table and a `gated-banner` slot. The rendering rule is mutually exclusive: a card either shows the gated banner OR the dimension table.

```html
<article class="job-card" data-tier="A" data-sort_date="2026-05-26" data-sort_company="Acme">
  {% if gate_violations %}
  <div class="gated-banner">🚫 Filtered out — work_arrangement, contract_type</div>
  {% else %}
  <div class="header">
    <div class="title">{{ job.title }}</div>
    <div class="score-pill tier-A">A</div>
  </div>
  <div class="meta">{{ job.company }} · {{ job.location }} · {{ job.posted_at }} · <a href="...">View posting ↗</a></div>
  <table class="dim-table">
    <tr class="dim-row dim-tier-A">
      <th>{{ dim_name_1 }}</th>
      <td><span class="tier-badge tier-a">A</span></td>
      <td class="evidence"><em>"<<evidence quote pulled from the JD>>"</em></td>
    </tr>
    <tr class="dim-row dim-tier-B">
      <th>{{ dim_name_2 }}</th>
      <td><span class="tier-badge tier-b">B</span></td>
      <td class="evidence"><em>"<<evidence quote pulled from the JD>>"</em></td>
    </tr>
    <!-- 3 more rows, one per remaining dimension from user-profile.dimensions[] -->
  </table>
  {% endif %}
</article>
```

The dimension names come from the workspace's `user-profile.json.dimensions[]` array (discovered at `/analyze-cv`) or, when absent, the universal bootstrap in `_job-matcher/references/dimensions-default.md`. The template does not name dimensions itself.

Class names:

- `.gated-banner` — left-bordered light surface, `var(--danger)` accent stripe.
- `.dim-table` — full-width, font-size 13px, no outer border. Compact row padding.
- `.dim-row.dim-tier-A` / `.dim-tier-B` / `.dim-tier-C` / `.dim-tier-D` — applied to the `<tr>` for optional row tinting.
- `.tier-badge.tier-a` / `.tier-b` / `.tier-c` / `.tier-d` — pill-shaped badge in the second column.
- `.evidence` — italic, `var(--text-muted)`, two quotes max per dimension.

The HTML card tier corresponds to the **overall** tier of the job (top right pill, derived from dimension tiers per the rule documented in the workspace's dimension reference).

The score-pill content changed in v0.8.0: it displays the **tier letter** (A/B/C/D) rather than a numeric score, since the v1 rubric is dimension-tier-based and the aggregate number was removed by design. As of v0.10.0 templates no longer emit `data-sort_score` — sorting uses `data-sort_date` and `data-sort_company`.

## `.job-card` — signal badges (Phase 12)

A/B-tier live cards carry an optional row of **signal badges** between the `.meta` line and the dimension table, surfacing the four optional Phase-12 scoring fields. The row reuses the existing `.tag-chip` / `.tag-chip.accent` primitives — **no new CSS**. The fields (and their enums) are the single-source-of-truth set in `../../shared-references/canonical-schemas.md` § "Canonical enums":

- `match_explanation_tag` (`all-fit` | `one-gap` | `multiple-gaps` | `overqualified` | `underqualified` | `trajectory-concern`) → `.tag-chip.accent`, hyphens rendered as spaces.
- `competitiveness` (`high` | `med` | `low`) → `.tag-chip` labelled `🎯 competitiveness: <value>`; the chip's `title` attribute carries `competitiveness_evidence` as a hover tooltip.
- `confidence` (`high` | `med` | `low`) → `.tag-chip` labelled `confidence: <value>`.

```html
<div class="signal-badges" style="margin-bottom:8px">
  <span class="tag-chip accent">one gap</span>
  <span class="tag-chip" title="Top Picks surfaced — under 10 applicants">🎯 competitiveness: high</span>
  <span class="tag-chip">confidence: med</span>
</div>
```

The whole row is guarded by `{% if job.tier in ['A','B'] and (job.competitiveness or job.confidence or job.match_explanation_tag) %}` and each chip by `{% if job.<field> %}`. **Back-compat:** the four keys are written lazily and **omitted (never `null`)** when not yet derived (see `canonical-schemas.md` § "Written lazily"); pre-Phase-A entries lack the keys entirely, so the row renders nothing and never errors. Badges appear only on the five **job-card** views (`match-jobs`, `job-search`, `check-job-notifications`, `deep-sweep`, `ultramode`) — never on `check-inbox`, `funnel-report`, or `interview-prep`, which render no job cards. **Within-tier ordering** (confidence high→med→low, then `posted_at` desc) is applied by each consuming command's payload-build step, not the template — see `../../shared-references/render-orchestration.md` § "Optional scoring signals + within-tier ordering".

## Markdown — dimension table

The corresponding markdown view renders the dimension table as a four-column markdown table per job:

```markdown
### 🟢 {{ job.title }} · {{ job.company }} (A)

| Dimension | Tier | Evidence |
|---|:---:|---|
| {{ dim_name_1 }} | **A** | _"<<evidence quote pulled from the JD>>"_ |
| {{ dim_name_2 }} | **B** | _"<<evidence quote pulled from the JD>>"_ |
| {{ dim_name_3 }} | **A** | _"<<evidence quote pulled from the JD>>"_ |
| {{ dim_name_4 }} | **B** | _"<<evidence quote pulled from the JD>>"_ |
| {{ dim_name_5 }} | **A** | _"<<evidence quote pulled from the JD>>"_ |
```

The number of dimension rows and their names come from the workspace's `user-profile.json.dimensions[]` (or the universal default if absent). The template iterates whatever is in the payload.

Gated jobs render as:

```markdown
### 🚫 Filtered out — {{ job.title }} · {{ job.company }}

- **<<gate_violation kind 1>>** — <<one-line reason>>
- **<<gate_violation kind 2>>** — <<one-line reason>>
```

## `source_chip()` macro (Phase 11)

A shared Jinja macro that turns a structured `source` object into a short, human-readable `.tag-chip` (HTML) or label (markdown). It is the single home for the structured-`source` → string rendering contract; templates **must never** interpolate `{{ job.source }}` directly, because the field is an object (`{lane, provider, board}`), not a string.

- **Where it lives:** implemented once in `templates/html/_macros.html.j2` and `templates/markdown/_macros.md.j2`. The shared bases (`base.html.j2`, `base.md.j2`) import it and re-export it as `source_chip`, so every Tier 1 view inherits it; views that render standalone (e.g. for verification) import the partial directly with `{% import "_macros.html.j2" as macros %}` and call `macros.source_chip(...)`. See `../../shared-references/workspace-layout.md` § "Template macro contract".
- **Input:** a structured `{lane, provider, board}` object, or — during the lazy tracker `2 → 3` upgrade — a bare legacy string.
- **Output rules:**
  - `lane == "linkedin"` → the `board` surface alone (e.g. `Top Picks`, `Search`) to preserve today's appearance.
  - external lane → `Provider · Board`, title-cased from the slugs (e.g. `Greenhouse · Miro`); the board is omitted when it equals the provider (e.g. `remoteok`/`remoteok` → `Remoteok`).
  - bare string → rendered verbatim.
  - empty / missing → renders nothing.

```html
<span class="tag-chip">Greenhouse · Miro</span>   <!-- {lane:"ats", provider:"greenhouse", board:"miro"} -->
<span class="tag-chip">Top Picks</span>           <!-- {lane:"linkedin", provider:"linkedin", board:"Top Picks"} -->
```

## `ultramode` view — unified multi-source results (Phase 11)

The `ultramode` view is `match-jobs` with source awareness. It reuses every job-card primitive (tier pill, "⚡ apply early" chip, dimension table, gated banner, "Filtered out" group, toolbar) and adds **only three** source-specific elements:

1. **Source chip** — `{{ macros.source_chip(job.source) }}` appended to the card's `.meta` line, so the list stays one unified ranking rather than per-source groups.
2. **"also seen on N"** — when `job.also_seen_on[]` is non-empty (other sources that surfaced the same role after dedupe), a `.tag-chip.accent` "also seen on N" indicator sits in the `.meta` line, with a secondary "Also on: …" line of source chips below the card body.
3. **"Apply at source ↗" CTA** — a `.copy-btn`-styled anchor to the canonical `job.url`, the direct apply route, distinct from the inline source chip.

```html
<article class="job-card" data-tier="A" data-sort_date="2026-06-15" data-sort_company="Vercel">
  <div class="header">
    <div class="title">Senior Backend Engineer <span class="tag-chip" style="background:var(--accent-from);color:#fff">⚡ apply early</span></div>
    <div class="score-pill tier-a">A</div>
  </div>
  <div class="meta">Vercel · Remote (Global) · $170–200k · 2026-06-15 · {{ macros.source_chip(job.source) }} · <span class="tag-chip accent">also seen on 3</span></div>
  <!-- dimension table … -->
  <div class="meta" style="margin-top:8px">Also on: {{ macros.source_chip(s) for s in job.also_seen_on }}</div>
  <div style="margin-top:10px"><a href="{{ job.url }}" class="copy-btn">Apply at source ↗</a></div>
</article>
```

The dispatcher pre-sorts `data.results` tier A→B→C, freshest-first within tier, gated last; the template renders in order and collapses any `gate_violations[]` entry into the "Filtered out" group. Worked payloads: `../examples/ultramode-{multi-source,gated,empty,also-seen}.json`.

