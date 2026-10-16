# Fleet — multi-worker coordination: liveness, storms, collisions, handoffs

One slide = one worker, end to end, backgrounded; keep the pool saturated. All
vision calls flock through a fleet-global gate, so worker count is not the
bottleneck. This file is the coordination law from five certified-deck
programs (~200 worker-runs, dozens of provider storms).

## WORKER LIVENESS CONTRACT (binding)

Liveness lives in the progress DB — never in file mtimes, UI state, or "no
completion notification". A build worker that touches the progress DB MUST use
the claim/heartbeat protocol (the DB helper's `claim`/`heartbeat`/`release`
subcommands):

1. `claim <slide> <self-generated-unique-id>` at start — it REFUSES if a
   DIFFERENT worker holds a fresh claim (that is a live peer: stand down
   read-only — the dual-dispatch law made flesh in the tool). Legacy rows
   without claims read as UNCLAIMED — claim them on first touch.
2. `heartbeat <slide> <id>` after every completed step and at least every
   ~10-15 min in long read/thinking phases (the ONLY liveness writer — bulk
   sync and content updates never touch it). A builder that pauses (long
   sleeps, hung probes, measurement marathons) MUST touch shared state anyway
   — DB updated_at bump, QA-dir timestamp touch, or a scratch heartbeat file —
   or liveness sweeps will call it dead and dispatch a duplicate over it.
3. `release <slide> <id>` at the end.
4. `set` refuses to write a row claimed by a live foreign worker (writers pass
   their owner id; the coordinator repairs with `--force`).
5. **Dispatchers claim atomically**: when a coordinator and a periodic
   watchdog can both dispatch the same unit, the coordinator sets the row
   state (gen_status=building) in the same breath as the worker launch — the
   builder's first file write is ~10 min later, and a watchdog sweeping
   meanwhile sees a dispatchable row that is already owned. The buildable
   query is a NECESSARY condition, never a sufficient one.

`set` syntax: `set <slide> <field> <value>` (three positionals —
operations.md); verify every write with a SELECT.

## What counts as death evidence

- **The only valid death test for agent workers is the dual condition**: ≥40
  min with ZERO file-artifact movement anywhere in the slide's namespace AND
  the DB row still mid-state (claim stale). Process absence is NOT death
  evidence for session-scoped agents — an agent between model calls holds NO
  process at all (a takeover justified by "zero live processes" was VOIDED
  when the "dead" peer wrote its build 30s later). Process-verified death is
  valid ONLY for process-bound workers (soffice, analysis/validation lanes,
  long-running shells).
- **"No completion notification" proves nothing** — notifications are lost (a
  fleet reported 6 live workers; ground truth 4; two dead workers' last writes
  made them look busy from their own side). "Stuck running" workers were often
  DONE — verify with sweeps + DB rows + non-blocking task-output probes before
  re-dispatching; a false "dead" call is what CREATES dual-worker collisions.
- **A worker's protocol has quiet phases** — probe ladders (up to 2h),
  sleep-300 re-probes, hang-retry walls of 450-540s each, measurement
  marathons. Before declaring death on 60 min of silence, check whether the
  last banked artifact is a terminal state the worker just hasn't recorded;
  prefer messaging the suspected-dead worker or waiting one cycle. If you
  must dispatch, scope the resume worker to VERIFICATION-FIRST with DB writes
  held.
- **The DB-vs-reality answer is `sweep`** (building rows classified live /
  ZOMBIE / unclaimed by heartbeat freshness, 40-min default). But during
  provider storms the sweep OVER-COUNTS zombies (heartbeats stall while
  workers sit in gate ladders) — file activity is the truth signal for agent
  workers mid-write; never re-dispatch no-notice/no-activity slides on the
  first storm sweep (they may be mid-ladder).
- **Compaction self-amnesia**: an agent's own "who wrote this" attributions are
  UNRELIABLE after long runs — a solo worker re-discovered its own
  certification chain as "peer writes" and nearly adopted them. Before
  treating observed fresh writes as a peer's, enumerate every candidate
  writer INCLUDING the observer itself (duration/mtime math: if only you were
  alive, it was you). Coordinators relaying state to long-running workers:
  include absolute mtimes and the full write-chain.

## Dispatch discipline

- Briefs are derived from THAT deck's `slide_dependencies.json` + instructions
  file + the actual raw/final — never from coordinator memory of another
  deck's families. **A slide number is not an identity across decks** (deck A's
  45 ≠ deck B's 45; pre-curation contact sheets ≠ current numbering). The
  buildable query is the dispatch oracle.
- Brief content lines come from the slide's own spec/frame — never
  reconstructed from stale numbering (workers verify anyway; wrong hints
  waste attention and invite second-guessing of correct specs).
- **Research fleets bank per unit**: any long-range subagent whose product is
  per-unit files finishes one unit COMPLETELY (the unit's provenance file
  written atomically: temp name → move) before starting the next; on provider
  errors sleep 120s and retry up to 3×, then mark `[?]` and move on — never
  abort the run; keep vision probes to 1/unit. Resume briefings are written
  from a DISK SWEEP, not from the dead agent's report. Parallel fleet size vs
  an actively-storming provider: stagger rather than fan all-at-once — a
  drowned fleet banks nothing.
- **Post-pass ownership**: before any post-pass (OMML wrap, graph embed)
  consumes a deliverable, check that no worker still owns that slide's files
  (fresh mtimes = an active owner; one alignment fixer rebuilt the pptx
  minutes after the wrapper agent was dispatched for it).

## Provider storms

- **Fleet-event signature**: a batch of same-duration agent failures (~19.3
  min, or 62-68 min, identical to the second) with "the upstream provider is
  temporarily unavailable" is the HARNESS's model upstream flapping — a fleet
  event, not N slide failures. Dying workers may bank NOTHING (verify disk
  before assuming partial work); other workers keep making calls throughout —
  live workers' file activity is the cheapest "is the provider back" probe.
- **Recovery order**: disk sweep per slide → file-activity liveness probe
  (10 min fresh = alive; no-activity AND no-notice = leave alone, may be
  mid-ladder) → ONE batch of resume workers, each with (a) an exact
  banked-state summary from the sweep and (b) a STORM-RESILIENCE clause: on
  provider/upstream errors sleep 120s and retry up to 3×, bank per step
  atomically, keep logs in the project scratch dir (never the host /tmp),
  never abort the run.
- **Probe-gated storm chain** (when the gateway walls every completion while
  `/v1/models` answers 200 in ms): each cycle runs a cheap 8-token text probe
  (75s cap); the REAL call fires only when a probe returns with a body; sleep
  120 between cycles; max 3 attempts per phase; DB claim heartbeated from
  inside the loop; all state in a storm_log the next worker reads.
  Distinguishes "gateway dead" (port down) from "upstream wedged" (port up,
  completions hang).
- **Banked-skip judge loops**: background judge loops reference the live
  render path and skip any transcript already containing FINAL VERDICT — no
  judge is paid for twice; a rebuild mid-storm is picked up automatically.
  ALWAYS verify which bytes a running judge read (`/proc/<pid> lstart` vs file
  mtime) before banking its verdict, and keep a crop transcript only if its
  region is pixel-identical across the rebuild (prove with a diff, don't
  assume).
- **Global interruptions** (host restart, session-wide freeze): the next
  sweep WILL double-dispatch whatever the coordinator also resumes —
  expected. Resume workers lead with a disk survey + verification of banked
  state, and treat a detected peer as "converge and verify", never "fight or
  restart". "All subagents interrupted" can be FALSE — background subagents
  may survive a host restart; sweep for survivors (file mtimes moving across
  the fleet, live soffice/python) before any mass resume.

## Collisions & the watch protocol

- **Two builders on one slide**: the claim-holder watches (claim + heartbeat
  stay fresh; poll ~10 min; 60-min-silence takeover rule); the ACTIVE builder
  proceeds. Conflict-free knowledge transfer is ONE notes file in the
  watcher's own scratch/QA space (evidence-cited divergences) — never the
  build dir, never deliverable paths. Takeover triggers, any one fires: (a)
  newest foreign artifact 60-min stale; (b) certification with a measured
  divergence VISIBLE — run the pixel audit of the certified render vs the
  original frame on exactly the known points, file an OBJECTION per the
  precision mandate (visible deviation = MAJOR even over a judge PASS),
  re-open the row, fix under the claim; (c) RELEASED marker / exit without
  certify. Archive the overridden build + script in the slide's QA dir (never
  delete); normalize at ship — the certified bytes must sit at the plain
  single-version name before any final-deck merge.
- **Pre-contract workers** (no claim file): the stand-down-on-fresh-writes
  read-only protocol. A silently-resumed original + a re-dispatched resume can
  both own one slide — let both finish, reconcile the DB row from the
  transcripts, bank BOTH evidence tracks (never merge/delete).
- **Contested certification**: verify WHAT BYTES the build actually consumed
  (require lines + mtimes + component header rationale) against the defect
  timeline — a self-contained build that consumed no tainted bytes is clean
  even without a marker.

## Handoffs & resumes

- **A handoff/journal is a LOWER BOUND on completed work**, written some time
  before death — re-measure the deck-wide invariant from the artifacts before
  acting on handoff lists (a dead wrapper's journal said 5 wrapped; disk had
  7; journal mtimes vs artifact mtimes exposed post-journal work), and treat
  "may have been missed" flags as unverified either way. Count
  multi-occurrence strings with `grep -o` (slide XML is one line — `grep -c`
  returns 1 for any hit).
- **A stale handoff summary is a hypothesis about disk state** — stat the
  deliverable, QA dir, and DB row BEFORE resuming any phase of a compacted
  task (one "mid-campaign" summary described a task certified 8 hours
  earlier). A dispatch's "expected" value is a claim to test, never a target
  to write — the frame wins over dispatches and transcriptions alike.
- **Resuming a dead builder: verify what the banked artifacts RENDER, not what
  their comments claim** — re-render the current pptx and md5-compare against
  the dead builder's last scratch render (byte-identical proves the
  "corrected" edit never changed output, so its closed-loop findings still
  apply). Keep the predecessor's attempt numbering when no QA evidence exists
  yet (attempt 1).
- **Resume from banked tables, re-derive only what fails**: the dead worker's
  banked DEFECTS/RESUME/measurement files make a cold start possible — trust
  banked rows over re-measuring; re-derive only geometry the rows disagree on
  or your own closed-loop checks fail. Resume from the RESUME log's NEXT line
  (append-one-line-per-step); adopt banked verdicts unless fresh evidence
  contradicts; when you deviate, state the deviation + evidence IN the resume
  entry so the log and the judge transcript tell one consistent story.
- **The marker is the LAST artifact**: complete the chain (reconstruct →
  verify with 0-diff render bindings → fresh judge → certify → write marker)
  — a marker without the transcript that justifies it misleads every
  provenance check keyed on it.
- **The owner's defect report, not the DB, is the state of record for a
  reported defect** — a DB `visual_check=PASS` can be a PRE-DEFECT PASS. A
  watchdog "repair" note in last_error referencing a superseded transcript is
  stale the moment a fresh judge lands: clear it at certification. Heartbeat
  files in the QA dir keep the watchdog from re-dispatching over a long
  judge-wait silence.
- **A banked-PASS row is terminal** — verifying beats re-judging; never
  rebuild over artifacts you cannot attribute (re-stat + read-first).

## Multi-lane shared state

- **Never in-place-edit shared ledgers under multi-lane concurrency** —
  append (e.g. `cat >>`), and re-read after any tool failure ("file modified
  since read" means a sibling lane wrote in between). An edit whose old text
  overlaps a sibling's line can SILENTLY DELETE it while reporting success:
  after ANY edit to a shared ledger, grep-count the neighboring entries you
  did not intend to touch, and keep the full text of any line you are about
  to replace in context so a loss is recoverable without archaeology.
- **Fabrication defense (a fleet worker fabricated an analysis artifact for
  a slide that does not exist)**: the never-invent law applies to PIPELINE
  ARTIFACTS too — any agent may fabricate plausible-looking JSON under
  pressure. Assert file counts against the deck's slide count after every
  sweep; sanity-check index metadata (kept frames must exist, timestamps
  inside a real group); DB rows upserted outside the registered index never
  drive dispatch (the buildable set gets cross-checked against the deck's real
  slide set). Fabricated files move (never delete) to a strays dir with a
  README; the row is marked blocked.
- **Evidence strays** are banked and reported, never silently cleaned
  (operations.md).

## Watchdog duties (every ~30 min)

Sync+report the DB; run the sweep — building rows with stale/missing
heartbeats are the re-dispatch list (resume rule: banked artifacts and attempt
numbering preserved, fresh worker verifies the banked state against its own
ground-truth frame before continuing); content-gate enforcement; house-chrome
conformance sweep on PASSed builds. The watchdog treats ANY fresh-activity
signal (files OR row) as owned and carries a hands-off list for workers it
knows are in long phases.
