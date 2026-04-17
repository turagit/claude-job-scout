# Featured Section

Loaded on demand by `_profile-optimizer/SKILL.md` when proposing or re-scoring this section.

---

Propose items based on CV content:
- Any portfolio links, publications, or projects mentioned in CV
- Suggest creating a case study from the CV's strongest achievement
- If CV mentions certifications, link to credential pages
- Target 3-5 featured items — these appear above the fold and drive engagement

### Templates

See `../banner-featured-templates.md` for the 5-slot Featured section framework and supporting-docs-to-slot mapping. Use the templates to propose specific Featured items backed by the user's indexed documents.

### Supporting-doc citations

When proposing Featured items, consult `.job-scout/cache/supporting-docs.json` (see `../../shared-references/supporting-docs.md` for the consumer contract). For each proposed item:

1. Check if the user's supporting-docs index contains a matching entry (by type: `cert` → Slot 1, `case_study` → Slot 2, etc.).
2. If a match exists, cite the source path in the proposal: "Feature your AWS SA Pro cert → source: `certs/aws-sa-pro.pdf`."
3. If no match exists but the slot is worth filling, suggest creating the asset (see template guidance above).

Add a **Supporting Doc** column to the proposal table:

```
| Current | Proposed | CV Source | Supporting Doc |
|---------|----------|-----------|----------------|
| (empty) | AWS SA Pro cert link | CV line 42 | certs/aws-sa-pro.pdf |
```
