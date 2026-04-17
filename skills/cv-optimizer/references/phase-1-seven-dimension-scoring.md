# Phase 1 — Deep Analysis (Seven-Dimension Scoring)

Loaded on demand by `cv-optimizer/SKILL.md`. Runs always unless a valid `.job-scout/cache/cv-analysis-<hash>.json` cache hit exists — in which case the cached result is used and this phase is skipped. Covers dimensions 1-7 with weights, inline examples, and references to `psychology-cheatsheet.md`, `action-verbs.md`, and `ats-keywords.md`.

---

### Seven-Dimension Scoring (1–10 each, weighted)

#### 1. ATS Compatibility (20%)
- **Standard section headings** recognized by all major ATS (Workday, Greenhouse, Lever, iCIMS, Taleo): "Professional Experience", "Education", "Skills", "Certifications" — not creative alternatives
- **Clean formatting:** single-column layout, no tables/text boxes/images/headers-footers (ATS strips them), standard fonts (Arial, Calibri, Garamond), consistent date format (MMM YYYY)
- **File format:** .docx preferred by ATS; .pdf acceptable if text-selectable (never scanned image PDFs)
- **Contact block:** name, email, phone, LinkedIn URL, city/country — on separate plain-text lines
- **No ATS poison:** avoid special characters in headings, embedded charts, multi-column layouts, creative icons

#### 2. Content Impact — Achievement Density (25%)
- **SPAR method:** Situation → Problem → Action → Result (evolution of PAR — the Situation anchors the story, making the impact more credible)
- Every bullet should contain a **quantified result** or a **tangible business outcome**
- Strong action verbs from `references/action-verbs.md` — never repeat a verb within the same role
- Zero filler phrases: eliminate "responsible for", "duties included", "helped with", "involved in", "assisted with"
- **Recency weighting:** current/most recent role gets 4–6 bullets, previous 3–4, older 2–3 (mirrors how recruiters actually read)

#### 3. Keyword Optimization (15%)
- Extract **hard skills, tools, certifications, methodologies** from target JD (if provided)
- Include both spelled-out and acronym forms: "Continuous Integration/Continuous Deployment (CI/CD)"
- Keywords woven **into achievement bullets** — not dumped in a skills-only section (ATS + humans both weight contextual usage higher)
- Target **75%+ keyword match** against the specific JD; **60%+** against the general role category from `references/ats-keywords.md`
- Never keyword-stuff: each keyword must appear in a truthful context

#### 4. Structure & Visual Hierarchy (10%)
- Reverse chronological within each section
- **F-pattern optimized:** most important info in the left-most, top-most positions (matches eye-tracking research: recruiters scan in an F-shape spending 6–7 seconds on initial scan)
- Consistent bullet style, indentation, spacing
- Strategic use of **bold** for company names, role titles, and key metrics — guides the eye to high-value content during the 7-second scan
- Target length: 1 page (0–5 yrs), 2 pages (5–15 yrs), 3 pages (15+ or academic only)

#### 5. Professional Positioning & Narrative (10%)
- **Professional summary** (3–4 lines): functions as a value proposition, not a bio. Opens with strongest credential, names the target role, includes 1 signature achievement with a number
- Complete contact info with LinkedIn URL
- No photos, DOB, marital status, nationality (unless required by local convention)
- **Career narrative coherence:** progression should tell a logical story — if it doesn't, the summary must frame the thread

#### 6. Psychological Persuasion Design (NEW — 10%)
Evidence-based techniques from behavioral psychology applied to CV content:

- **Anchoring Effect:** Lead each role with the most impressive metric — it sets the reference point for everything that follows. If you "Grew revenue 340%", put it first; subsequent bullets inherit its halo.
- **Peak-End Rule:** The first bullet of your most recent role and the last line of your CV (often the education section or a closing skills block) are disproportionately remembered. Make them count.
- **Social Proof:** Named clients, Fortune-500 logos, user counts, team sizes, and recognizable brands all trigger trust heuristics. "Led migration for a FTSE-100 bank" beats "Led migration for a financial client."
- **Specificity Bias:** Specific numbers feel more credible than round ones. "Reduced latency by 37%" is more believable than "Reduced latency by about 40%." Use precise numbers wherever honestly possible.
- **Contrast Effect:** Place your strongest achievement immediately after the role title — the reader's baseline expectation for a bullet is low, so a strong number creates a positive surprise.
- **Loss Aversion Framing:** Frame achievements in terms of what would have been lost without you: "Prevented £2M revenue loss by identifying and resolving critical payment-processing bug within 4 hours" triggers loss-aversion more powerfully than "Saved £2M."
- **Authority Signals:** Certifications, publications, speaking engagements, "selected for", "appointed to", advisory roles — these trigger the authority heuristic. Place them where they'll be seen.
- **Scarcity & Exclusivity:** "One of 3 engineers selected for..." or "Invited to join founding team..." signals selectivity.

#### 7. Recruiter Experience & Readability (NEW — 10%)
Optimized for the human who reads *after* the ATS passes:

- **7-Second Scan Test:** Can a recruiter extract role, seniority, top 3 skills, and one impressive number within 7 seconds? If not, restructure.
- **Jargon calibration:** Match the terminology level to the likely first reviewer (HR screens need broader terms; hiring-manager screens can handle deep technical language). When in doubt, use both: "Implemented event-driven architecture (Kafka, SNS/SQS) to handle 50k events/sec."
- **White space discipline:** Cramming text reduces readability. If cutting content is needed to fit page count, cut the weakest bullets — don't shrink font or margins below 10pt/0.5in.
- **Consistent tense:** Past tense for all previous roles, present tense for current role only.
- **No orphan sections:** Every section should have at least 2 items. One-item sections look thin.

---
