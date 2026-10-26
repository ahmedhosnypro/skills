# doc-parse — reliability notes

Lane reliability discipline for parse and judge calls through the
configured document-parse endpoint. Every law below is measured on
the slide-JPEG reference corpus; parse strategy lives in the parse
playbook, adjudication law and defect vocabulary in the process
notes. The script and its config are frozen — reliability fixes are
procedural, never script edits.

## The lane model

- All calls share one route. A lane is the pair (route, load window):
  the same route behaves differently across load windows, so the
  window is a first-class variable in every reliability decision,
  not noise.
- Per-page latency is tens of seconds. A multi-page batch is a
  background job, never a foreground drip.
- Every call carries its own record (see "Per-call record" at the
  end). Without the record a hang cannot be classified and a retry
  cannot be justified.

## Probe-first gate

- **Before any heavy call — a big image, a big prompt, a long judge
  leg — fire a tiny cheap probe on the same route** (and the same
  image where the route is image-bound): a minimal ask that a healthy
  route serves in seconds.
- A probe pass is: exit 0, a non-degenerate transcript, zero
  degenerate events. Bank the probe's record like any other call.
- **A green probe does NOT guarantee the heavy call — it only proves
  the route is alive.** Measured on the reference corpus: a probe
  passed in ~2 s and the heavy call fired in the same serving window
  hung to its full wall timeout. The probe gate is necessary hygiene,
  not a guarantee.
- On a hang: one paced re-probe — wait ~60 s, re-probe. If the
  re-probe is green, gate the lane behind probes: every subsequent
  heavy call on that lane waits for its own green probe first.
- Keep every command's paths absolute, so a caller bug (missing file,
  stale directory) is never mistaken for a lane failure.
- Verify a fallback model with its own tiny probe before relying on
  it. On the reference corpus a fallback family was independently
  dead — its own tiny probe read-timed out — which its first heavy
  failure alone could not have distinguished from a lane wedge.

## Hang taxonomy

Classify every hang from its record — exit code, transcript size,
stderr signature — and record which form it took, before deciding
what to do next. Two forms exist:

- **Timeout-hang** — the explicit timeout is reached and observed: a
  wall-timeout wrapper yields exit 124, the transcript is zero bytes.
  Stderr is either silent (startup line only) or shows a transport
  abort line, then silence to the wall.
- **Empty-response hang (the JSON surface's zero-delta form)** — the
  connection closes with a zero-byte or undecodable body and no
  content: the lane's retry ladder burns its attempts, and the call
  fails silently or cascades into upstream gateway errors
  (unreachable, timeout, restart races).

Both forms share the decisive property: **zero content bytes were
produced.** The surface is JSON-only — no streaming arm, no partial
read to salvage — so classification comes from the record, and the
explicit wall timeout is the only thing that makes a hang observable
and classifiable.

- **A hang is a LANE event, never a model verdict and never a model
  failure.** No verdict is fabricated for a blocked leg; the leg's
  frozen prompt and retry recipe are banked instead.
- The affected page is re-probable: it returns to the probe-and-rerun
  pool and counts out of every done metric until a clean transcript
  exists. A hung page is never a silent gap in coverage and never a
  "no result".
## Retry recipes

- **Explicit timeouts on every call.** The parse script's `--timeout`
  (default 150 s) bounds the HTTP read; judge legs and batch wrappers
  carry an explicit wall timeout too. An un-timed wedged call is
  unobservable; a timed one becomes a classified, banked failure.
- **Single paced retries.** A fixed wait (~60 s), then ONE retry into
  a fresh call directory. Never overwrite or reuse a call directory —
  every attempt keeps its own record.
- **A second identical hang stops the lane.** Two identical hangs in
  one window mean the lane is wedged: archive the stderr, bank the
  call records, close the leg with honest debt labels, and stop
  spending retries in that window.
- **After repeated hangs in a window, the only banked clear-lever is
  a different time window — schedule the retry later.** Byte-freeze
  the prompt and inputs first, so the window retry is a re-run of the
  exact call, not a redesign.
- **Do not treat hangs as size failures.** The size hypothesis is
  refuted on the reference corpus: tiny probes completed green inside
  the bad window while heavy calls hung with identical signatures,
  and far heavier calls completed normally in healthy windows;
  splitting a hanging prompt into byte-frozen halves changed nothing.
  The wedge tracks request class × load window, never prompt bytes —
  do not spend retries on size-reduction variants of a hanging call.
- **Classify before retrying.** A wedge hang (change the window), an
  upstream error cascade (bank and back off — on HTTP 429/5xx wait
  ~60 s, at most 3 attempts, then bank the failure as a recorded
  blocker), and a caller bug (fix the invocation) are different
  events with different recipes.
- **Retry budget discipline.** A failed call gets one recipe retry;
  beyond that, escalation is a window change or an explicitly
  recorded blocker — never an unbounded loop of identical attempts.

## Bounded parallel fan

- **Parse calls inside one worker MAY run concurrently.** Batch them
  in ONE shell invocation with background jobs and `wait`, capped at
  FOUR in flight against the one endpoint, refilling freed slots
  until the batch is done:

```sh
# four parse calls in flight against one endpoint, then wait
python3 <skill-dir>/scripts/parse_document.py p01.jpg -o out/call01 &
python3 <skill-dir>/scripts/parse_document.py p02.jpg -o out/call02 &
python3 <skill-dir>/scripts/parse_document.py p03.jpg -o out/call03 &
python3 <skill-dir>/scripts/parse_document.py p04.jpg -o out/call04 &
wait
```

- Measured on the four-slide cascade corpus: **2.3–2.9× wall-clock
  speedup per slide run (per batch 1.6–3.1×) with no fidelity loss** —
  every fan call exited 0 with clean finish reasons, corroboration
  re-parses came back byte-identical, and composed outputs showed no
  ordering artifacts.
- **Evidence the gain on every batch.** Report the batch's wall-clock
  next to the sum of the calls' individual latencies — the speedup is
  that measured ratio from call records, never an assumption.
- The four-in-flight cap is protection, not an optimum (see "Honesty
  boundaries").
- **Vision-judge legs stay sequential** — one in flight. On the
  reference corpus the sequential judge legs dominated the closing
  wall, and heavy full-frame judge legs serialize across workers by
  gateway policy.
- **Cross-worker fan-out against one shared upstream stays gated** by
  the gateway's caller policy: the in-worker fan is sanctioned; a
  cross-worker fan is not unbidden.
- **Corpora-sized batches are a background job — keep working.**
  Dispatch the batch, then continue other work; never sit idle on
  one call when sibling calls can run in the same fan.
## Determinism and corroboration

- **Identical re-passes return byte-identical content.** Measured on
  the reference corpus three ways: the same input at three output
  budgets produced md5-identical transcripts; retry pairs were
  byte-identical; a repetition loop reproduced byte-identically
  across budgets.
- **A second identical read is TRANSPORT corroboration only.** It
  proves the call reproduced — never that the content is true.
  Systematic blind spots reproduce as faithfully as the text they
  hide: on the reference corpus, hallucinated strings and identical
  coordinate offsets passed through both reads of a byte-identical
  pair untouched. Agreement between identical reads measures
  deterministic repetition, not confirmation.
- **Independent confirmation needs a different read:**
  - a different input form — defect-targeted region crops were the
    only lever that ever produced new ground-truth strings on the
    dense reference slides;
  - an independent vision check — a vision subagent adjudicating the
    doubtful string against the image;
  - a different `max_output_tokens` only after byte-wise
    verification: a higher budget is NOT automatically a different
    read (whole transcripts were byte-identical across 1024 / 3000 /
    9000 on two reference slides), so verify the delta before
    counting it as corroboration.
- **When two reads contradict, both are advisory.** Banked
  counter-instance: one reference slide showed pass instability — its
  low-budget read caught most ground-truth strings while its
  higher-budget read collapsed to a minimal read, dropping agreement
  to near zero. Observed full-frame outcomes were exact identity or
  large divergence, never small drift. A contradiction is never
  settled by repeating either read; a different-form read
  adjudicates, and until then every verdict from the pair stays
  single-read.
- A repetition loop that fills the token ceiling is deterministic
  too: the same short prefix repeats to any budget, byte-identically.
  That is a budget-dial and input-form question — the loop recipe
  lives in the parse playbook.

## Judge-driven prompt loop

- **Multi-round judging against ground truth refines targeting —
  regions, anchors, the input form, the judge's own instructions —
  never the wire contract.** The full doctrine, measured gains, stop
  rules, and blocked-leg banking live in process-notes.md
  (judge-loop doctrine).

## Honesty boundaries

- **Caps and thresholds are protection, not optima.** The
  four-in-flight cap, the probe gate, the retry counts, and the
  round caps are measured-to-work protections against shared-lane
  failure modes. Word them as caps ("capped at four in flight"),
  never as tuned optima.
- **Claims the corpus could not measure stay out of law.** On the
  reference corpus these stayed graded, and they are worded that way
  wherever they appear: an endpoint-cache explanation for a ~35×
  latency spread on byte-identical output (hypothesis); whether the
  serving route streams deltas for large vision-token requests (open
  question); prompts banked but never re-run in a healthy window
  (banked-untested). Label the grade or leave the claim out.
- **Failure is reported, never absorbed.** A hung, looped, or empty
  call is banked with its record and counted out of every done
  metric — never silently dropped, never re-labeled as a model
  verdict, never averaged away inside a success rate.
- A blank or degenerate result on a text-bearing page is a FAIL,
  never a "no result".

## Per-call record

- One directory per call, nothing ever overwritten: command,
  start/finish timestamps, exit code, stdout, stderr, transcript,
  and finish reason. A retry lands in a fresh directory.
- **Per-page stderr lines are the reliability data** — count and
  carry them; they are what makes a hang classifiable and a retry
  justifiable.
- Failed pages stay out of every done counter until a clean
  transcript exists.
- Latency expectation: tens of seconds per page. A call far beyond
  that without output is a suspected hang — check for deltas before
  waiting out the full wall.
