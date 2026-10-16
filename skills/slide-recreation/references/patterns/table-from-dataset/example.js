// Pattern: table-from-dataset
// When a slide shows rows of a KNOWN dataset, every table cell comes from the
// ONE canonical dataset file — read live at build time. Never hardcode sample
// rows from a spec (specs are lossy and can carry shifted/wrong values that a
// lenient judge will pass).
// Run:  NODE_PATH=$(npm root -g) node example.js   -> demo_table.pptx
// Then: python3 assert_cells.py demo_table.pptx <csv>
//
// LAWS:
// - ONE canonical file per dataset; tables AND graphs read the same file
//   (cross-slide consistency).
// - Build reads the CSV live: validate the header, index rows, every displayed
//   cell = CSV[row].field verbatim. Only the DISPLAYED row set is hardcoded.
// - Derive an ambiguous displayed row set from geometry + class-color
//   forensics (band counts, per-block color composition, dataset class
//   boundaries) — never from a guess.
// - Self-check asserts EVERY cell: extract the table from the built pptx XML
//   (a:tbl nests deeper than graphicFrame/a:tbl) and compare against the CSV
//   (assert_cells.py). A whole-number convention must match the original
//   (e.g. "5" not "5.0").
// - Dense tables get a zoomed crop comparison BEFORE the full-slide judge
//   (see dense-region-crop-compare) — full-slide calls cannot resolve 8pt cells.

const fs = require("fs");
const pptxgen = require("pptxgenjs");

// ---- parameters ----------------------------------------------------------------
const CSV = process.argv[2] || "demo_iris.csv";
const COLUMNS = ["sepal_length", "sepal_width", "species"];   // displayed columns
const ROWS = [0, 1, 2, 44, 99];                              // displayed row indices

// ---- build ----------------------------------------------------------------------
const lines = fs.readFileSync(CSV, "utf8").trim().split(/\r?\n/);
const header = lines[0].split(",");
if (header.slice(0, 4).join(",") !== "sepal_length,sepal_width,petal_length,petal_width") {
  throw new Error("canonical header mismatch — refusing to build from a wrong file");
}
const DATA = lines.slice(1).map((l) => l.split(","));

const fmt = (v) => (Number.isInteger(Number(v)) ? String(Number(v)) : v);  // "5" not "5.0"

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
const s = pres.addSlide();
s.background = { color: "E8E8E8" };

const tableRows = [header.filter((h) => COLUMNS.includes(h))];
for (const i of ROWS) tableRows.push(COLUMNS.map((c) => fmt(DATA[i][header.indexOf(c)])));

s.addTable(tableRows, {
  x: 1.0, y: 1.5, w: 8.0,
  fontSize: 10, fontFace: "Arial", color: "333333",
  border: { type: "solid", color: "999999", pt: 0.5 },
  margin: 0.04,
});

pres.writeFile({ fileName: "demo_table.pptx" })
  .then(() => console.log("wrote demo_table.pptx — now run assert_cells.py"));
