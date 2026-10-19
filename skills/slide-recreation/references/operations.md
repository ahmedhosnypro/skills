# Operations — endpoint quirks, retries, workspace environment

## Model endpoint facts (hard-won)

- **Always stream.** Aggregating gateways commonly cut non-streaming responses
  at ~60s (`ServiceTimeout` while the key pool churns). Streaming works.
- `finish_reason=length` + `content=null` + filled `reasoning_content` = the
  model spent its whole budget thinking → raise max-tokens. **BUT many
  endpoints' completion ceiling is ~32k tokens regardless of the request**
  (measured: `usage.completion_tokens=31999` at a requested 65536) — dense
  specs sitting near the ceiling are a retry-variance problem, not a budget
  problem: re-run rather than raising max-tokens further; a persistent failure
  means the SPEC is too dense for one completion and needs a re-analysis pass.
- A text model sometimes returns empty content with a parse error "Expecting
  value: line 1 column 1" — transient; re-run the pass (it retries only
  missing outputs).
- ~540 vision tokens/frame at 960px JPEG q4.

## Retry/idempotency patterns

- Analysis/validation passes are idempotent (skip existing outputs) — the
  documented retry path is just re-running them; delete a slide's raw to force
  that slide's re-analysis. Ranged validation runs rewrite the combined
  aggregate → re-aggregate after every ranged run (pipeline.md).
- **`find -newermt '-60 minutes'` silently returns nothing** — compute an
  explicit timestamp: `SINCE=$(date -d '-60 minutes' '+%Y-%m-%d %H:%M')` then
  `find ... -newermt "$SINCE"`.
- **When the interactive shell is zsh**, unquoted `$var` does NOT word-split,
  so for-loop one-liners (montage over N files, `$files` expansions) fail with
  the whole list as one argument. Run loops via `bash -c '...'` or zsh's
  `${=files}`.
- **A progress-DB `set` takes THREE positionals** (`set <slide> <field>
  <value>`) — a `field=value` form silently no-ops when piped through `tail`;
  verify every "update" with a SELECT/read-back.

## Workspace environment

- Video ids are nested for multi-course projects: `VIDEO =
  <course>/<lecture-dir>` — a bare lecture id joins a nonexistent dir and the
  DB open fails. Everything a command touches stays inside one video's
  namespace; parallel videos' DBs never collide.
- **`TMPDIR` must be redirected into project scratch** for the vision gate, LO
  sessions, and big shell heredocs — a quota-limited or broken host /tmp kills
  them SILENTLY. A transient "disk quota exceeded" mid-lane with parallel
  lanes rendering is usually the shared per-user quota capping — retry after
  ~1 min before diagnosing, and clean only your OWN staging dirs.
- **Web research is best-effort, never a hard dependency**: if the search tool
  401s even after a token refresh during a work window, proceed on the
  already-ratified plan — never block a validated plan on research tooling
  (judges + PIL confirmations catch a wrong choice). On an auth failure:
  refresh the token/session once, retry, then proceed. The full mandated-research
  protocol (sources/ layout, SOURCES.md, trust + economy laws) lives in
  `references/source-research.md`.
- API key file at the project root (mode 600); env override supported; never
  commit or log it.
- `frames/` is gitignored and huge — never re-extract or re-download.
- LibreOffice render route quirks (private profile, short-home workaround,
  placeholder renders) live in building.md "Rendering infra".

## Curation / evidence traps

- Curated decks get renamed ("the badge numeral = the number printed on the
  original"), and old numbering leaves landmines:
  - Banked QA evidence under an old slide number may belong to a DIFFERENT
    slide after curation (one real deck: slide 53's banked evidence belonged
    to current slide 41). Always verify banked evidence against your own
    ground-truth frame before resuming — **a file name is not provenance; the
    ground-truth frame is**.
  - A prior worker's build may be from the OLD deck entirely. Resume rule:
    verify the build matches your ground truth, not just the file name.
  - Never delete old-numbered artifacts — archive them (old analysis dirs,
    `*.db.bak`, old builds, old QA dirs) and keep a new2old mapping JSON
    (recovery law: pipeline.md).
- Evidence strays (a ground-truth frame banked under another slide's QA dir)
  are BANKED and listed in the close-out report, never silently "cleaned".
- A `SOURCES.md.tmp` with fully-banked references may be promoted to
  `SOURCES.md` only after checking every referenced artifact exists on disk
  (the research happened; only the atomic rename was missing).

## Multi-worker coordination

The worker fleet (liveness contract, storms, collisions, handoffs, provenance)
has its own reference: **fleet.md**. DB commands are namespaced per video
(`VIDEO=<id> <progress-db> <cmd>`) so parallel videos never collide.
