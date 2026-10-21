# Render validation

The structural validator proves a diagram is *well-formed*. It does not prove the
diagram *draws*. Render validation is the second gate: run the diagram through a real
renderer and confirm it produces output without a parse or layout error.

## Three gates

| Gate | Tool | What it proves | Needs |
|---|---|---|---|
| 1 — structure | `scripts/validate-mermaid.ts` (Bun) | Keyword declaration, fence closure, non-emptiness, no bare-arrow edges | Nothing beyond the skill itself |
| 2 — render | `scripts/mmdr.sh` → `mmdr` (native Rust) | The diagram actually parses to IR and lays out to SVG/PNG | The launcher; it uses a `PATH` `mmdr` or fetches one into a per-user cache |
| 3 — portability | `mmdc` (mermaid.js) or Mermaid Live Editor | The diagram parses under the engine GitHub, GitLab and editors actually run | A browser-capable machine, or manual checking |

Gate 3 is the one that matters when the diagram publishes to a GitHub-family
surface. `mmdr` is lenient in specific grammars — it draws diagrams mermaid.js
rejects — so gates 1 and 2 can both be green on a diagram that GitHub shows as a
parse error. Run gate 3 before publishing to an issue, PR, README, wiki or GitLab.

Gate 1 is mandatory and always available. Gate 2 is mandatory work: the launcher makes the
binary available, so the only remaining reason to skip gate 2 is a machine that cannot
reach GitHub — and then you say so. Never pass a diagram that has only cleared gate 1
without saying so.

Gate 1 never renders anything — it must not be used as evidence that a diagram draws.

The five verified non-portable constructs are pinned as fixtures in
`tests/mermaidjs-parity/defects/*.mmd`, gated by
`tests/mermaidjs-parity/parity.test.ts`. That suite fails when no reachable
renderer detects one of them, so it catches a regression in a grammar or a
renderer swap — and it records which gate caught each defect.

## Install `mmdr` — the launcher handles it

The skill ships `scripts/mmdr.sh`, a launcher that makes the render gate work
without a manual install:

- **Already installed?** It execs `mmdr` straight from `PATH` — zero overhead, zero downloads.
- **Not installed?** On first use it resolves the latest release from the GitHub Releases
  API, downloads the asset matching your platform, extracts the single binary into a
  per-user cache (`$XDG_CACHE_HOME` or `~/.cache`, under `mermaid-diagrams/`), and reuses
  that cache on every later run. No `sudo`, no package manager, nothing written outside
  the cache.

So the normal path is simply:

```sh
<skill-dir>/scripts/mmdr.sh --version
```

That both verifies the binary and warms the cache. Everything below passes the same flags
through to the real renderer.

### When fetching fails

The launcher reports the reason and exits nonzero — it never silently skips gate 2.
Causes and remedies:

| Cause | What to do |
|---|---|
| No network | Install manually, or use a documented fallback renderer |
| GitHub API rate-limited | Retry later, or install manually |
| Missing `curl`/`tar` (`unzip` on Windows) | Install that host tool — the launcher names it |
| Read-only `HOME` with no writable cache | Set `XDG_CACHE_HOME` to a writable directory |

Manual install, when you prefer to own the binary: the [releases
page](https://github.com/1jehuang/mermaid-rs-renderer/releases) carries one asset per
platform — `mmdr-x86_64-unknown-linux-gnu.tar.gz`, `mmdr-aarch64-unknown-linux-gnu.tar.gz`,
`mmdr-x86_64-apple-darwin.tar.gz`, `mmdr-aarch64-apple-darwin.tar.gz`,
`mmdr-x86_64-pc-windows-msvc.zip`, `mmdr-aarch64-pc-windows-msvc.zip`. Package managers
also carry it: `cargo install mermaid-rs-renderer`, `brew tap 1jehuang/mmdr && brew install
mmdr`, `scoop bucket add mmdr https://github.com/1jehuang/scoop-mmdr`, `yay -S mmdr-bin`
(Arch), and `nix profile install github:1jehuang/mermaid-rs-renderer`. Once `mmdr` is on
`PATH`, the launcher defers to it and never fetches anything.

Because the cache is per-user and per-version, upgrades happen automatically the next time
a new upstream release appears — and an old cached binary keeps working meanwhile.

## The render check

Every command below runs the launcher. It forwards the arguments to the real renderer,
using a `PATH` `mmdr` when one exists and the cached binary otherwise, so the commands
read the same either way. Render to a disposable artifact in the system temp directory,
or pipe to stdout, so no output is written into the project tree:

```sh
# single diagram file → stdout
scripts/mmdr.sh -i diagram.mmd -e svg

# stdin render (cheapest smoke test for one diagram)
echo 'flowchart LR; A-->B' | scripts/mmdr.sh -e svg

# whole-file → stdout, no disk write
scripts/mmdr.sh -i diagram.mmd -e svg > /dev/null && echo rendered
```

A nonzero exit means the diagram failed gate 2. Fix the diagram — the message names the
offending construct — and re-run both gates.

**A zero-byte output is a failure, not a pass.** The renderer can exit 0 while writing
nothing when the flag combination is wrong. Confirm the output is non-empty — a bare
`-e svg | wc -c` — or check the file exists, before recording gate 2 as passed.

## Batch-render a Markdown document

Every fenced mermaid block inside a Markdown file renders in one process:

```sh
scripts/mmdr.sh -i README.md -o out.svg -e svg
```

This is also the fastest way to render-check a doc containing many diagrams: render each
block once rather than splitting them by hand. Two rules hold, both learned from the
released binary rather than its README:

- **`-o` is mandatory for markdown input.** Without it, `mmdr` exits 0 and writes zero
  bytes — a silent pass that would let a broken diagram through. Always pass `-o`.
- **`-o` names a file, not a directory, and you get one numbered output per block.** Given
  `-o out.svg`, two blocks produce `out-1.svg` and `out-2.svg` next to it. The upstream
  README advertises a directory mode; the released build does not implement it. Check the
  output files exist before calling the document rendered.

PNG output is available with `-e png`; the default is SVG. `-w`/`-H` (not `--width`/
`--height`) force explicit output dimensions — otherwise the output keeps the diagram's
natural dimensions. Built-in theme presets are available via `-t` (default, dark, forest,
neutral, modern), applied before any config-file or init overrides.

## Supported diagram types

`mmdr` covers the diagram kinds this skill documents, plus a few it does not:

flowchart/graph, sequenceDiagram, classDiagram, stateDiagram-v2, erDiagram, pie, gantt,
journey, timeline, mindmap, gitGraph, xychart-beta, quadrantChart, sankey-beta, kanban,
C4Context (and the C4 family), block-beta, architecture-beta, requirementDiagram,
zenuml, packet-beta, radar-beta, treemap.

Types outside that list have no `mmdr` coverage. The C4 family renders through mmdr, but
read the caveats below before trusting C4 output for publication.

## Configuration

`mmdr` takes configuration through a JSON file passed with `-c`, not through Mermaid
frontmatter:

```sh
scripts/mmdr.sh -i diagram.mmd -o out.svg -e svg -c render-config.json
```

```json
{
  "themeVariables": {
    "primaryColor": "#F8FAFF",
    "primaryTextColor": "#1C2430",
    "primaryBorderColor": "#C7D2E5",
    "lineColor": "#7A8AA6",
    "background": "#FFFFFF",
    "fontFamily": "Inter, system-ui, sans-serif",
    "fontSize": 13
  },
  "preferredAspectRatio": "16:9",
  "flowchart": {
    "nodeSpacing": 50,
    "rankSpacing": 50
  }
}
```

Spacing can also be set per invocation without a config file:

```sh
scripts/mmdr.sh -i diagram.mmd -o out.svg -e svg --nodeSpacing 60 --rankSpacing 120
scripts/mmdr.sh -i diagram.mmd -o out.svg -e svg --preferredAspectRatio 16:9
```

`--fastText` uses calibrated fallback widths for ASCII labels instead of loading the
font database. It is the fastest path, but label metrics differ slightly — use it for
render gates, not for producing shipped assets.

## Styling and directives

`mmdr` supports the styling directives this skill uses: `classDef`, `class`,
`:::class`, `style`, `linkStyle`, and `%%{init}%%` directives (JSON5 tolerated). It also
supports the full flowchart node-shape and edge-style vocabulary.

## Where mmdr differs from mermaid.js

`mmdr` is not a drop-in model of the reference renderer. The differences below matter
whenever the output is published on a surface that renders with mermaid.js — GitHub
issues, pull requests, READMEs and wikis, GitLab, VS Code, Notion, Obsidian, Confluence.

- **No ELK layout.** `mmdr` has one layout engine and no ELK configuration key, so the
  strategies this skill's theming reference documents (`SIMPLE`, `NETWORK_SIMPLEX`,
  `LINEAR_SEGMENTS`, `BRANDES_KOEPF`) cannot be selected against it. It does handle
  subgraph `direction` overrides, nested subgraphs, and automatic spacing.
- **No `look: handDrawn`.** The sketch look has no mmdr equivalent; the classic output is
  the only one.
- **`mmdr` is lenient where mermaid.js is strict.** It parses and draws diagrams that
  mermaid.js rejects, so a clean `mmdr` run does not prove a diagram renders on GitHub.
  Verified non-portable constructs, each of which `mmdr` accepts and mermaid.js does not:
  - `sankey-beta` has no `title` statement. Remove the line; title the diagram through
    frontmatter or config instead.
  - `xychart-beta` y-axis bounds take `-->`, never a word: `y-axis "Label" 0 --> 500`.
  - `requirementDiagram` attribute values are identifier tokens, so `id: RQ-1` splits at
    the hyphen and fails to parse. Quote any value that needs punctuation.
  - `radar-beta` labels come from `curve id[Display label] {…}` or `curve "Label" {…}`;
    do not rely on a lenient renderer to display what upstream will not parse.

When a diagram depends on ELK or handDrawn appearance, or will render on a GitHub-family
surface, publish with `mmdc` (below) rather than `mmdr`, and render-check with both.

Two further behavioral notes:

- mmdr's parser is strict in places, too. It can reject syntax mermaid.js accepts. A
  rejection is a real finding worth fixing, but confirm before declaring a diagram
  broken: run it in the Mermaid Live Editor, and report both outcomes when they disagree.
- Visual fidelity is still catching up to mermaid-cli in areas; treat mmdr output as
  structurally authoritative and visually indicative until upstream reports otherwise.

## Fallback renderers

When the launcher cannot produce a renderer — no network and no cached binary — these are
the documented fallbacks, in order:

1. **Mermaid CLI (`mmdc`)** — the reference renderer: it runs the same mermaid.js engine
   GitHub does. It requires headless Chromium via Puppeteer, so the machine must have the
   browser or depend on a Docker image that bundles it. The usual failure is "Could not
   find Chromium"; fix it by installing the browser's system libraries or pointing at an
   installed executable through a Puppeteer config file. On a full shared `/tmp`
   (`tmpfs`) Chrome also fails to spawn with an empty stderr — set `TMPDIR` to a
   directory with space.

   ```sh
   mmdc -i diagram.mmd -o out.svg
   ```

   Two traps when scripting the reference check: **`mmdc` exits 0 even when the diagram
   fails to parse**, and **it leaves the previous output file on disk when a run fails** —
   so reusing one output path makes a failed render look like a pass. Always render to a
   fresh path and assert the output is non-empty.

2. **Mermaid Live Editor** — paste the source and check the render. No install, but not
   automatable and not offline.

Always tell the user which renderer validated the diagram, and that mmdr was unavailable
when it was skipped. A render gate that silently disappears is a gate that stopped
existing.
