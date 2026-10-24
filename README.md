# skills

My agent skills, published through GitHub and [skills.sh](https://skills.sh).
One repo, one `skills/` directory, one version line per skill.

## Skills

### doc-parse

Agent skill for parsing document images (slides, scans, forms, tables,
charts, rendered pages) into structured markdown with the nemotron-parse
model family, then auditing the parse against its source image: a frozen
in-skill script, an owner-provisioned endpoint config the agent never
touches, transcript-only outputs, a five-stage parse → adjudicate →
register workflow, and a defect vocabulary for reading-order, table,
coordinate, and hallucination findings.

```sh
npx skills add ahmedhosnypro/skills --skill doc-parse
```

### photocraft-automation

Agent skill for [PhotoCraft](https://github.com/storytold/photocraft) — drive
the image editor end-to-end, and develop it: triage bugs, verify fixes, file
upstream issues. Includes the call-logging corpus, the wedge diagnostic
doctrine, the visual loop, a cross-project sqlite issue tracker, and a
machine-local runtime home shared by every install.

```sh
npx skills add ahmedhosnypro/skills --skill photocraft-automation
```

### photocraft-art-director

Agent skill — the creative-director brain for PhotoCraft artwork. Drafts
the direction charter for a piece (subject-fitted composition grammar, frozen
medium declaration, derived palette and light invariants, pixel-verifiable
acceptance budgets), resolves any artistic intent to the exact PhotoCraft
command via the skill's own search index, and drives the audit → pixel-probe
→ adjudicate → surgical-fix loop to certification. Must fire before
starting, planning, or revising any artwork built with PhotoCraft.

```sh
npx skills add ahmedhosnypro/skills --skill photocraft-art-director
```

### mermaid-diagrams

Agent skill for authoring and validating Mermaid diagrams — every supported
diagram type, from flowcharts to the full C4 architecture family, with a
bundled offline structural validator (runs under [Bun](https://bun.sh);
falls back to `mmdc` or the [Mermaid Live Editor](https://mermaid.live) when
Bun is unavailable).

```sh
npx skills add ahmedhosnypro/skills --skill mermaid-diagrams
```

### pooled-missions

Agent skill for running any decomposable mission with a fixed-size pool of
parallel background subagents — code or non-code — tracked in a per-run
sqlite DB with crash-safe resume, one uniform worker protocol, and a final
gated verification. Bundles a tracking-DB helper (`scripts/pool-db.sh`);
falls back to a plain-file mode when sqlite3 is unavailable.

```sh
npx skills add ahmedhosnypro/skills --skill pooled-missions
```

### skill-self-improve

Agent skill for distilling a skill's accumulated self-improvement logs —
amendment blocks, process notes, evolution logs, memory dirs, judge
templates, worklogs, DEFECTS/RESUME scratch output — back into the skill
itself, running the collect → analyze → fold-back improvement loop. Use it
to improve, harvest, or audit any skill's evolution; initial authoring of a
new skill belongs to the skill-creator discipline instead.

```sh
npx skills add ahmedhosnypro/skills --skill skill-self-improve
```

### slide-recreation

Agent skill for recreating slides as high-fidelity PowerPoint (PPTX) files
from existing slide images, screenshots, or lecture-video frames — the full
rebuild pipeline: frame extraction, perceptual-hash dedup, a mandatory human
review gate, vision-model analysis, text-model validation, pptxgenjs build,
LibreOffice headless render, closed-loop pixel checks, and visual-judge
certification against the original; plus 2D professional math equations
(mathtext to PNG with an editable-OMML upgrade), algorithm-generated graph
images (the real algorithm on real data), dependent-slide component
inheritance, multi-worker fleet coordination, and a byte-verbatim final-deck
merge gated at zero mismatched pixels. When a deck's instructions mandate it,
an optional web-verified source-research layer runs alongside analysis:
web-search the primary source behind every slide, confirm content against the
fetched source, bank the source's own figures under sources/slide_NNN_source/
with a SOURCES.md provenance record per slide plus a fleet-level source map.
Bundles certified equation renderers
(`scripts/render_eq*.py`) and a 16-entry runnable pattern library; ships its
own authoring gate (`assets/verify_skill.sh`).

```sh
npx skills add ahmedhosnypro/skills --skill slide-recreation
```

### visual-judge

Agent skill for judging, scoring, verifying, or auditing images and
screenshots under a rigorous verdict protocol: render-vs-original and
implementation-vs-design comparison verdicts (PASS/FAIL), rubric-scored
quality inspections (0-10 axes, READY/NEEDS FIXES), visual launch gates, and
defect registers in which every vision-model claim is adjudicated against
objective measurement before it counts. Harness-generic: needs only a
vision-capable reader that returns text, plus file storage; every fancier
route is an optional accelerator.

```sh
npx skills add ahmedhosnypro/skills --skill visual-judge
```

## Install

Install one skill by name with the
[skills CLI](https://github.com/vercel-labs/skills):

```sh
npx skills add ahmedhosnypro/skills --skill <skill-name>
```

Preview what a skill contains without installing:

```sh
npx skills add ahmedhosnypro/skills --list
```

The skills provide instructions and helper scripts only; they do not install
PhotoCraft, Bun, or any renderer, and they never manage tokens.

## Layout

```text
skills/
  photocraft-automation/   SKILL.md, config.example.json, assets/,
                           scripts/issues_db.py, utils/
  photocraft-art-director/ SKILL.md, indexer/, references/
  mermaid-diagrams/        SKILL.md, scripts/ (validator + tests),
                           assets/, references/
  pooled-missions/         SKILL.md, scripts/pool-db.sh,
                           assets/verify_skill.sh
  skill-self-improve/      SKILL.md, references/, assets/verify_skill.sh
  slide-recreation/        SKILL.md, scripts/render_eq*.py,
                           assets/verify_skill.sh, references/
                           (incl. the 16-pattern example library)
  visual-judge/            SKILL.md, references/, assets/verify_skill.sh
```

Maintained by [@ahmedhosnypro](https://github.com/ahmedhosnypro).
MIT licensed — see [LICENSE](LICENSE).
