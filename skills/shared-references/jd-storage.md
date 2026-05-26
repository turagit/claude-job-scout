# JD Storage (hybrid)

> **The full JD text lives outside `tracker.json`.** Metadata stays in the tracker entry; the JD blob lives at `.job-scout/jds/<job_id>.txt`. The tracker entry's `jd_path` is the pointer.

## Why hybrid

`tracker.json` is read on every dedupe pass — every command that touches LinkedIn listings loads it. JD blobs are large (~3–8KB each). 770 jobs × 5KB = ~4MB of JD text loaded on every dedupe read if stored inline. Move blobs out: dedupe stays cheap, JD reads are lazy per-job.

The v1 contract (in the old `tracker-schema.md`) said "description is written once, by the first ingestion skill that fully extracts the job." Live state shows zero of 770 jobs have a description stored — the inline-write contract silently failed. The hybrid layout enforces the write because the absence of a sibling file is visible at a glance.

## File layout

```
.job-scout/
  jds/
    <job_id>.txt        # plain-text JD blob. UTF-8. Whatever LinkedIn rendered.
    <job_id>.meta.json  # optional companion: extracted-at, applicant-count snapshot, posting-date
```

## Write contract

Any ingestion skill that has the full JD in hand MUST write it before persisting the tracker entry:

```bash
write_jd() {
  local ws=".job-scout"   # workspace .job-scout/ root
  local jid="$1"          # job id
  local jd_text="$2"      # the full JD text

  mkdir -p "$ws/jds"
  printf '%s\n' "$jd_text" > "$ws/jds/$jid.txt.tmp"
  mv "$ws/jds/$jid.txt.tmp" "$ws/jds/$jid.txt"
  echo "jds/$jid.txt"   # caller writes this string to tracker.jobs[$jid].jd_path
}
```

The tracker entry must then have `jd_path: "jds/<job_id>.txt"` set in the same atomic write.

## Read contract

Skills that need the full JD (`/cover-letter`, `/interview-prep`, `_job-matcher` evidence-quote extraction) MUST:

1. Read `tracker.jobs[jid].jd_path`.
2. If non-null, read the file at `<workspace>/.job-scout/<jd_path>`.
3. If null (legacy entry), the skill must trigger fresh extraction via the Chrome extension and backfill — same as the v1 contract said for missing descriptions.

## Migration of existing entries

All 770 existing entries have `description: <empty or absent>`. They are tagged `jd_path: null` by the migration. On next interaction with each job, the consuming skill fetches the JD and backfills `jd_path`. There is no batch backfill — the cost is paid lazily on access.

## Retention

JDs are never deleted by the plugin. The user may prune `.job-scout/jds/` manually; the only consequence is that downstream commands re-extract on demand.
