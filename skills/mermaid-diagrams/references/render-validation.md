# Render validation

The structural validator proves a diagram is *well-formed*. It does not prove the
diagram *draws*. Render validation is the second gate: run the diagram through a real
renderer and confirm it produces output without a parse or layout error.

## Two gates

| Gate | Tool | What it proves | Needs |
|---|---|---|---|
| 1 — structure | `scripts/validate-mermaid.ts` (Bun) | Keyword declaration, fence closure, non-emptiness, no bare-arrow edges | Nothing beyond the skill itself |
| 2 — render | `mmdr` (native Rust) | The diagram actually parses to IR and lays out to SVG/PNG | The `mmdr` binary, installed once |

Gate 1 is mandatory and always available. Gate 2 is mandatory work but conditional on
the binary: when `mmdr` is missing, use a fallback renderer (below) and tell the user
which one you used. Never pass a diagram that has only cleared gate 1 without saying so.

Gate 1 never renders anything — it must not be used as evidence that a diagram draws.

## Install `mmdr` (once, user-mediated)

`mmdr` ships as a single static binary per platform. The [releases
page](https://github.com/1jehuang/mermaid-rs-renderer/releases) carries one asset per
target; pick the one matching your platform:

| Platform | Release asset |
|---|---|
| Linux x86_64 | `mmdr-x86_64-unknown-linux-gnu.tar.gz` |
| Linux arm64 | `mmdr-aarch64-unknown-linux-gnu.tar.gz` |
| macOS x86_64 | `mmdr-x86_64-apple-darwin.tar.gz` |
| macOS arm64 | `mmdr-aarch64-apple-darwin.tar.gz` |
| Windows x86_64 | `mmdr-x86_64-pc-windows-msvc.zip` |
| Windows arm64 | `mmdr-aarch64-pc-windows-msvc.zip` |

Package managers also carry it: `cargo install mermaid-rs-renderer`, `brew tap
1jehuang/mmdr && brew install mmdr`, `scoop bucket add mmdr
https://github.com/1jehuang/scoop-mmdr`, `yay -S mmdr-bin` (Arch), and
`nix profile install github:1jehuang/mermaid-rs-renderer`.

The user drives the install once — this skill never installs software. Because the binary is
the user's, its freshness is theirs too: `mmdr` tracks upstream releases, not this skill's
version line, so a local `mmdr` may be older than the release table above.

## Detect before you use

```sh
mmdr --version
```

No binary, no render gate — fall through to the fallback list below and report it. Do not
attempt to download or build the binary from inside a rendering task.

## The render check

Render to a disposable artifact in the system temp directory, or pipe to stdout, so no
output is written into the project tree:

```sh
# single diagram file → stdout
mmdr -i diagram.mmd -e svg

# stdin render (cheapest smoke test for one diagram)
echo 'flowchart LR; A-->B' | mmdr -e svg

# whole-file → stdout, no disk write
mmdr -i diagram.mmd -e svg > /dev/null && echo rendered
```

A nonzero exit means the diagram failed gate 2. Fix the diagram — the message names the
offending construct — and re-run both gates.

## Batch-render a Markdown document

Every fenced mermaid block inside a Markdown file, in one process:

```sh
mmdr -i README.md -o diagrams/ -e svg
```

When `-o` names a directory, `mmdr` writes one numbered file per block
(`diagrams/diagram-1.svg`, `diagrams/diagram-2.svg`, …). This is also the fastest way to
render-check a doc containing many diagrams: render each block once rather than splitting
them by hand.

PNG output is available with `-e png`; the default is SVG. `--width`/`--height` force
explicit output dimensions — otherwise the output keeps the diagram's natural dimensions.

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
mmdr -i diagram.mmd -o out.svg -e svg -c render-config.json
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
mmdr -i diagram.mmd -o out.svg -e svg --nodeSpacing 60 --rankSpacing 120
mmdr -i diagram.mmd -o out.svg -e svg --preferredAspectRatio 16:9
```

`--fastText` uses calibrated fallback widths for ASCII labels instead of loading the
font database. It is the fastest path, but label metrics differ slightly — use it for
render gates, not for producing shipped assets.

## Styling and directives

`mmdr` supports the styling directives this skill uses: `classDef`, `class`,
`:::class`, `style`, `linkStyle`, and `%%{init}%%` directives (JSON5 tolerated). It also
supports the full flowchart node-shape and edge-style vocabulary.

## Where mmdr differs from mermaid.js

Two gaps matter when the output ships, because they are the main differences between
mmdr and the reference renderer:

- **No ELK layout.** `mmdr` has one layout engine and no ELK configuration key, so the
  strategies this skill's theming reference documents (`SIMPLE`, `NETWORK_SIMPLEX`,
  `LINEAR_SEGMENTS`, `BRANDES_KOEPF`) cannot be selected against it. It does handle
  subgraph `direction` overrides, nested subgraphs, and automatic spacing.
- **No `look: handDrawn`.** The sketch look has no mmdr equivalent; the classic output is
  the only one.

When a diagram depends on ELK or handDrawn appearance, publish with `mmdc` (below) rather
than `mmdr`, and render-check with both.

Two further behavioral notes:

- mmdr's parser is strict. It can reject syntax mermaid.js accepts. A rejection is a
  real finding worth fixing, but confirm before declaring a diagram broken: run it in
  the Mermaid Live Editor, and report both outcomes when they disagree.
- Visual fidelity is still catching up to mermaid-cli in areas; treat mmdr output as
  structurally authoritative and visually indicative until upstream reports otherwise.

## Fallback renderers

When `mmdr` is not installed, these are the documented fallbacks, in order:

1. **Mermaid CLI (`mmdc`)** — requires headless Chromium via Puppeteer, so the machine
   must have the browser or depend on a Docker image that bundles it. The usual failure
   is "Could not find Chromium"; fix it by installing the browser's system libraries or
   pointing at an installed executable through a Puppeteer config file.
   ```sh
   mmdc -i diagram.mmd -o out.svg
   ```
2. **Mermaid Live Editor** — paste the source and check the render. No install, but not
   automatable and not offline.

Always tell the user which renderer validated the diagram, and that mmdr was unavailable
when it was skipped. A render gate that silently disappears is a gate that stopped
existing.
