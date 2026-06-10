# Theme Tokens — Modern Cards

Single source of truth for visual design across all rendered HTML reports. Every per-view template uses these tokens via `var(--name)` — no view defines its own colors, fonts, or spacing.

The full token set is implemented as CSS custom properties in `../assets/theme.css`. This file is the conceptual reference; `theme.css` is the implementation.

## Colour tokens

| Token | Value | Use |
|-------|-------|-----|
| `--bg-page` | linear-gradient(180deg, #fff 0%, #f5f3ff 100%) | Page background |
| `--bg-card` | #ffffff | Card surfaces |
| `--surface-soft` | #f5f3ff | Subtle inner surfaces (chip backgrounds, hover states) |
| `--accent-from` | #7c3aed (violet 600) | Primary gradient start, A-tier pill, link colour |
| `--accent-to` | #ec4899 (pink 500) | Primary gradient end |
| `--accent-warn` | #fbbf24 (amber 400) | B-tier pill background |
| `--accent-warn-fg` | #78350f (amber 900) | B-tier pill text |
| `--accent-mute` | #9ca3af (gray 400) | Muted accents (e.g., flat-delta indicator) |
| `--text-strong` | #1f1f2e | Body text, titles |
| `--text-muted` | #6b7280 | Secondary text, metadata lines |
| `--ring-soft` | rgba(124, 58, 237, 0.10) | Card borders, divider lines |
| `--shadow-card` | 0 1px 3px rgba(0,0,0,.04), 0 8px 24px rgba(124,58,237,.08) | Card shadow |

## Geometry tokens

| Token | Value | Use |
|-------|-------|-----|
| `--radius-card` | 12px | Card corners, fold containers |
| `--radius-pill` | 999px | Score pills, tag chips, toolbar buttons |

## Typography tokens

| Token | Value | Use |
|-------|-------|-----|
| `--font-sans` | 'Inter', -apple-system, system-ui, sans-serif | Body text, titles |
| `--font-mono` | 'JetBrains Mono', 'SF Mono', monospace | Score values, metric numbers, timestamps |

## Tier-colour mapping

The tier comes from the `_job-matcher` v1 rubric and is passed in `inputs.data` as an uppercase `tier` string. Templates render the tier pill with a class derived from the lowercased tier:

| Tier | Pill class | Pill background |
|------|------------|-----------------|
| A | `score-pill tier-a` | violet→pink gradient |
| B | `score-pill tier-b` | amber |
| C | `score-pill tier-c` | grey |
| D (gated) | `score-pill tier-d` | muted |

Templates never compute the tier themselves — they trust the dispatcher's `tier` field.

## Print mode

`@media print` rules in `theme.css`:
- Page background → white.
- Hover effects removed.
- Toolbar and copy buttons hidden.
- Folds forced open.
- Cards get a 1 px solid border instead of shadow.
- `page-break-inside: avoid` on cards and folds.
