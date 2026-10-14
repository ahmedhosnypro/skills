# Improvement-mechanics taxonomy

The recurring self-improvement mechanics this skill distills. Use it as a
checklist when analyzing a corpus (Step 2): for each mechanic, decide
whether the target skill already has it, has a degraded version, or lacks
it — then feed the gaps into the fold-back plan.

## 1. Amendment discipline

Append-only, dated, evidence-motivated amendment blocks in the stable
core: title, motivating evidence, what supersedes what, version bump, a
supersession pointer left on the superseded text. The universal change
unit for skills that improve themselves. Degenerate forms to watch for:
silent rewrites (history lost), loud restatements (bloat, no new
information), amendment blocks without evidence (opinion, not harvest).

## 2. Write fence / role separation

Core files are law, amended only under the authoring discipline; agents
may append to the memory layer; scripts are owner-only. The structural
fix for mid-lane script patching is the fence plus a proposals bank
(banked proposal format: Evidence / Problem / Proposed change / Risk),
with applied changes recorded for an audit trail — not exhortation.

## 3. Two-tier storage

A stable protocol layer (byte-stable across copies in a healthy family)
separate from a growing doctrine layer (memory, vocabularies, evolution
log). When every clone of a skill shares one identical reference file,
that file is the stable core; when every clone diverges in another area,
that area is the growing layer. Use this signature to decide what goes
where in any skill.

## 4. Append-only asset layers with fixed entry formats

- Memory dirs: read before the task, append after every task, four-field
  entry (Context / Mistake with a measured number / Fix / Rule).
- Issue vocabularies: append-only, re-read before appending, frozen per
  round and bumped between rounds, near-duplicates recorded as
  "confirms <tag>" notes.
- Process notes: dated sections; superseded rules become pointers.
- Evolution log: one dated row per lesson, each with a "landed:" pointer
  to where the lesson ended up in the skill.

## 5. Promotion-on-recurrence

Lessons graduate from memory to stable core only on recurrence or
generalization. A dedicated maintenance pass (not a mid-task edit) does
the promoting, records landing locations, and ports canon candidates
into their parent-canon homes with a no-op check first, then per-file
verification.

## 6. Judge / verdict law

Objective pre-check gate before judging; content-anchored prompts;
explicit PASS semantics and retry budgets with park-and-report; measured
instrument readings outrank judge opinion; judges never re-litigate what
the pre-check measures. Judge templates and rubrics are versioned assets
grown under the same append-only rules.

## 7. Evidence-first scratch conventions

Worklogs (plan, no-op check, gate checks, landing record), resume
checkpoints (claim ids, checkboxes, measured values, explicit NEXT),
defects tables (method stated up front, evidence-linked rows, precision
wins), child→parent finding propagation, failure autopsies feeding
redesign, durable trackers that survive context compaction.

## 8. Machine verification of edits

Frontmatter YAML parse + discovery check after every edit (a parse
failure silently removes a skill from discovery), grep for surviving
contradicted prose, diff banks of the edits, and the skill's own verify
gate run with the exit code captured explicitly.

## 9. Transplant / port doctrine

Loader-path verification before install, dependency porting (never
improvise a mid-lane replacement), an adaptation note recording what was
ported and changed, head→canon propagation direction, per-tenant version
suffixes for clone families.

## 10. Knowledge accretion for large corpora

Index file plus numbered topical shards mapped to scenarios; failure-fix
walkthrough cases; guides (anti-patterns, FAQ, validation checklist);
templates. Accretes by ADDING shards rather than amending one body — the
pattern for skills whose subject matter grows without bound.

## 11. Anti-bloat checks

Line-count pressure is visible long before a cap is hit: repeated
sections, restated rules, vocabulary duplicates, amendment tails longer
than the body. Dedup, supersede, freeze templates per round, and
condense the canon as a first-class maintenance action.

## 12. Self-grading

A skill can carry its own evaluation methodology: scoring axes, what the
objectives measure versus what judgment covers, and a grading file that
any agent can run to assess whether the skill itself is performing.
