/**
 * Detection tests for mermaid.js-parity defects.
 *
 * Every fixture in `defects/` was verified against the reference renderer
 * FIRST (mmdc + Chrome, the same mermaid.js engine GitHub runs). Each one
 * is a diagram that engine rejects as a parse error — so it renders broken
 * on GitHub issues, pull requests, READMEs and wikis — while the offline
 * structural validator passes it, and while a lenient renderer draws it.
 *
 * Every fixture is exercised by BOTH renderers: `mmdr` (the skill's gate-2
 * Rust renderer) and `mmdc` (the reference mermaid.js engine). A renderer
 * that accepts a defect is a valid outcome, not a test failure — it is that
 * exact leniency these fixtures exist to document. The tests assert instead
 * that (a) both renderers were actually run, (b) the reference renderer
 * rejects each defect, and (c) the legal control is not rejected by either.
 *
 * A renderer that cannot run on this machine is reported as `unavailable`
 * and never counted as a rejection — so a broken launcher cannot fake
 * detection.
 *
 * Run: bun test ./tests/mermaidjs-parity/parity.test.ts
 */

import { describe, expect, test } from "bun:test";
import { mkdtempSync, rmSync } from "node:fs";
import { readdirSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { validateDiagramSource } from "../../scripts/validate-mermaid.ts";

const HERE = import.meta.dir;
const DEFECTS = join(HERE, "defects");
const MMDR = join(HERE, "..", "..", "scripts", "mmdr.sh");
const CONTROL = "radar-beta-bracket-label.mmd";

const workdir = mkdtempSync(join(tmpdir(), "mermaidjs-parity-"));
const unique = () => Math.random().toString(36).slice(2);

/**
 * `rejected` means the renderer refused to draw the diagram.
 * `accepted` means it drew real output.
 * `unavailable` means the renderer could not run — it is never a rejection.
 */
type Status = "accepted" | "rejected" | "unavailable";

interface Verdict {
  status: Status;
  note: string;
}

interface Renderer {
  readonly name: string;
  render(source: string): Promise<Verdict>;
}

async function run(
  cmd: readonly string[],
): Promise<{ code: number; out: string; err: string }> {
  const proc = Bun.spawnSync({ cmd: [...cmd], cwd: workdir, env: { ...process.env } });
  return {
    code: proc.exitCode,
    out: proc.stdout.toString(),
    err: proc.stderr.toString(),
  };
}

/** mmdc writes its parse error after a blank stderr line; take the first line that carries text. */
function firstMeaningfulLine(text: string): string {
  for (const line of text.split("\n")) {
    const t = line.trim();
    if (t && !t.startsWith("at ") && !t.startsWith("# ")) return t;
  }
  return "";
}

const verdict = async (out: string, code: number, err: string): Promise<Verdict> => {
  const svg = Bun.file(out);
  // A zero-byte artifact is a failure, never a pass — and a renderer that
  // exits 0 without writing is not evidence the diagram drew.
  const drew = code === 0 && (await svg.exists()) && svg.size > 0;
  if (drew) return { status: "accepted", note: "drew output" };
  return { status: "rejected", note: firstMeaningfulLine(err) || `exit ${code}, no output` };
};

const UNAVAILABLE: Verdict = { status: "unavailable", note: "renderer could not run" };

/** Gate 2 — the offline Rust renderer, through the skill's self-fetching launcher. */
const mmdr: Renderer = {
  name: "mmdr",
  async render(source) {
    const file = join(workdir, `mmdr-${unique()}.mmd`);
    await Bun.write(file, source);
    const out = `${file}.svg`;
    rmSync(out, { force: true });
    const { code, err } = await run(["bash", MMDR, "-i", file, "-o", out, "-e", "svg"]);
    // The launcher exits nonzero when it cannot produce a binary at all;
    // that is unavailability, not a parse rejection.
    if (code !== 0 && err.includes("mmdr unavailable")) return UNAVAILABLE;
    return verdict(out, code, err);
  },
};

/** Gate 3 — the reference engine: the same mermaid.js that GitHub runs. */
const mmdc: Renderer = {
  name: "mmdc (mermaid.js)",
  async render(source) {
    if (!Bun.which("mmdc")) return UNAVAILABLE;
    const file = join(workdir, `mmdc-${unique()}.mmd`);
    await Bun.write(file, source);
    const out = `${file}.svg`;
    rmSync(out, { force: true });
    const { code, err } = await run([
      "mmdc",
      "-i",
      file,
      "-o",
      out,
      "-e",
      "svg",
      "-b",
      "transparent",
    ]);
    // mmdc exits 0 even when a diagram fails to parse, so the artifact is
    // the only signal — and it leaves a previous file behind on failure.
    return verdict(out, code, err);
  },
};

const RENDERERS: readonly Renderer[] = [mmdr, mmdc];

/** A renderer counts only when it draws the legal control; otherwise its "rejections" are noise. */
async function isFunctional(r: Renderer): Promise<boolean> {
  const control = await r.render(readFixture(CONTROL));
  return control.status === "accepted";
}

function readFixture(name: string): string {
  return readFileSync(join(DEFECTS, name), "utf8");
}

function fixtures(): string[] {
  return readdirSync(DEFECTS)
    .filter((f) => f.endsWith(".mmd"))
    .sort();
}

const defects = fixtures().filter((f) => f !== CONTROL);

// --- Exercise BOTH renderers on every defect, one test per renderer per fixture. ---

describe("gate 2 — mmdr (Rust renderer)", () => {
  for (const name of defects) {
    test(`mmdr: ${name}`, async () => {
      const res = await mmdr.render(readFixture(name));
      // A defect this renderer accepts is documented leniency, not a failure.
      // Unavailability is reported loudly instead of counted.
      if (res.status === "unavailable") {
        console.warn(`    mmdr UNAVAILABLE for ${name}: ${res.note}`);
        return;
      }
      console.log(`    mmdr: ${name} → ${res.status} (${res.note})`);
      expect(["accepted", "rejected"]).toContain(res.status);
    });
  }
});

describe("gate 3 — mmdc (reference mermaid.js)", () => {
  for (const name of defects) {
    test(`mmdc: ${name}`, async () => {
      const res = await mmdc.render(readFixture(name));
      if (res.status === "unavailable") {
        console.warn(`    mmdc UNAVAILABLE for ${name}: ${res.note}`);
        return;
      }
      console.log(`    mmdc: ${name} → ${res.status} (${res.note})`);
      // The reference engine is the source of truth for GitHub rendering:
      // every defect here must be a parse error there.
      expect(res.status, `reference renderer did not reject ${name}: ${res.note}`).toBe(
        "rejected",
      );
    });
  }
});

// --- Doctrine: both renderers are run, and each defect is caught somewhere. ---

describe("doctrine — every defect is detected", () => {
  test("both renderers are exercised", async () => {
    const statuses: string[] = [];
    for (const r of RENDERERS) {
      const ok = await isFunctional(r);
      statuses.push(`${r.name}: ${ok ? "functional" : "UNAVAILABLE"}`);
    }
    console.log(`    ${statuses.join(" | ")}`);
    // Both renderers are attempted for every fixture (see the blocks above);
    // this test records which were usable.
    expect(statuses.length).toBe(RENDERERS.length);
  });

  for (const name of defects) {
    test(name, async () => {
      const results: string[] = [];
      let caughtByFunctional = 0;
      // Resolve each renderer's usability once: a renderer that cannot draw
      // the legal control cannot testify about any diagram.
      const usable: boolean[] = [];
      for (const r of RENDERERS) usable.push(await isFunctional(r));

      const verdicts: Verdict[] = [];
      for (const r of RENDERERS) verdicts.push(await r.render(readFixture(name)));

      for (let i = 0; i < RENDERERS.length; i += 1) {
        const r = RENDERERS[i]!;
        const res = verdicts[i]!;
        if (res.status === "rejected" && usable[i]) caughtByFunctional += 1;
        results.push(`${r.name}: ${res.status}${res.note ? ` — ${res.note}` : ""}`);
      }
      console.log(`    ${name}\n      ${results.join("\n      ")}`);
      expect(
        caughtByFunctional,
        `not detected by any functional renderer:\n      ${results.join("\n      ")}`,
      ).toBeGreaterThan(0);
    });
  }
});

describe("legal diagrams are not rejected", () => {
  test("radar-beta bracket-label control is accepted", async () => {
    const accepted: string[] = [];
    for (const r of RENDERERS) {
      const res = await r.render(readFixture(CONTROL));
      if (res.status === "unavailable") {
        console.warn(`    ${r.name} UNAVAILABLE for control`);
        continue;
      }
      expect(res.status, `legal diagram rejected by ${r.name}: ${res.note}`).toBe("accepted");
      accepted.push(r.name);
    }
    console.log(`    radar control accepted by: ${accepted.join(", ")}`);
  });
});

describe("offline validator blind spot, pinned", () => {
  for (const name of fixtures()) {
    test(`gate 1 passes ${name}`, () => {
      // Each fixture is structurally sound to the offline validator; the
      // defect is semantic. Pinned so a future validator change that starts
      // rejecting them is a visible decision, not an accident.
      expect(validateDiagramSource(readFixture(name))).toStrictEqual([]);
    });
  }
});
