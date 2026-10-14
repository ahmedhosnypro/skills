#!/usr/bin/env python3
"""Contract tests for mind_index.py (indexer-tester).

Real sqlite files in tmpdirs + a stub /embeddings HTTP server (stdlib only).
The stub returns deterministic float vectors and asserts every request body
carries "encoding_format": "float".
"""

import contextlib
import importlib.util
import io
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

INDEXER_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIND_INDEX = os.path.join(INDEXER_DIR, "mind_index.py")

spec = importlib.util.spec_from_file_location("mind_index", MIND_INDEX)
mi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mi)

# Deterministic vector map: first trigger substring found in the input text
# wins, else a default vector. All vectors share one dimension.
VECTORS = {
    "zingyfruit": [0.9, 0.1, 0.0, 0.0],
    "apple": [1.0, 0.0, 0.0, 0.0],
    "orange": [0.0, 1.0, 0.0, 0.0],
}
DEFAULT_VECTOR = [0.0, 0.0, 1.0, 0.0]
DIM = len(DEFAULT_VECTOR)


def vector_for(text):
    for trigger, vec in VECTORS.items():
        if trigger in text:
            return list(vec)
    return list(DEFAULT_VECTOR)


class StubEmbedServer:
    """POST /embeddings stub. behavior:
    "ok"               -> always 200 with deterministic vectors
    "flake2"           -> first 2 POSTs 403, then 200
    "always403"        -> every POST 403
    "probe_ok_then_403"-> first POST 200, every later POST 403
    Every request body is asserted to carry "encoding_format": "float".
    """

    def __init__(self, behavior="ok"):
        self.behavior = behavior
        self.calls = []
        self.bad_bodies = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                n = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(n)
                try:
                    payload = json.loads(body.decode("utf-8"))
                except Exception:
                    payload = None
                if not isinstance(payload, dict) \
                        or payload.get("encoding_format") != "float":
                    outer.bad_bodies.append(payload)
                outer.calls.append(payload)
                self._respond(outer.reply(payload))

            def _respond(self, reply):
                status, data = reply
                raw = json.dumps(data).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def log_message(self, *a):
                pass

        def reply(payload):
            idx = len(outer.calls)  # 1-based: current call already appended
            if outer.behavior == "always403" \
                    or (outer.behavior == "flake2" and idx <= 2) \
                    or (outer.behavior == "probe_ok_then_403" and idx > 1):
                return 403, {"error": {"message": "forbidden by stub"}}
            texts = payload.get("input", []) if isinstance(payload, dict) else []
            return 200, {
                "object": "list",
                "model": payload.get("model", "stub"),
                "data": [
                    {"object": "embedding", "index": i,
                     "embedding": vector_for(str(t))}
                    for i, t in enumerate(texts)
                ],
            }

        self.reply = reply
        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(
            target=self.server.serve_forever, daemon=True)
        self.thread.start()

    @property
    def url(self):
        host, port = self.server.server_address[:2]
        return f"http://{host}:{port}"

    @property
    def n_calls(self):
        return len(self.calls)

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)


def make_record(family, command, title, oneliner, body="", keywords=(),
                order=0):
    return {
        "path": f"{family}/{command}",
        "family": family,
        "command": command,
        "title": title,
        "oneliner": oneliner,
        "params_md": body,
        "traps_md": "",
        "intents": [],
        "keywords": list(keywords),
        "order": order,
    }


def write_slice(tmpdir, name, records):
    path = os.path.join(tmpdir, name)
    with open(path, "w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec) + "\n")
    return path


APPLE = make_record(
    "paint", "brush-apple", "Apple Brush", "Paint an apple orchard slice",
    "## Params\n- size of the apple orchard\n\n```\nplain code line\n```",
    keywords=["apple", "orchard"], order=1)
ORANGE = make_record(
    "paint", "pot-orange", "Orange Pot", "Shape a citrus orange pot",
    "## Params\n- zest of the citrus peel", keywords=["orange", "citrus"],
    order=2)
GLAZE = make_record(
    "glaze", "drip-honey", "Honey Drip", "Glaze with a honey drip coat",
    keywords=["honey", "glaze"], order=0)


class IndexerCase(unittest.TestCase):
    """Base fixture: tmpdir, stub embed server, CONFIG_PATH patched to a tmp
    config pointing at the stub (the real config.json is never touched)."""

    behavior = "ok"

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="mi-test-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.stub = StubEmbedServer(self.behavior)
        self.addCleanup(self.stub.close)
        cfg_path = os.path.join(self.tmp, "config.json")
        with open(cfg_path, "w", encoding="utf-8") as fh:
            json.dump({"base_url": self.stub.url, "model": "stub-embed",
                       "api_key": "k", "timeout_s": 10}, fh)
        self._old_cfg = mi.CONFIG_PATH
        mi.CONFIG_PATH = cfg_path
        self.addCleanup(self._restore_cfg)
        self.db = os.path.join(self.tmp, "index.sqlite")

    def _restore_cfg(self):
        mi.CONFIG_PATH = self._old_cfg

    def cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), \
                contextlib.redirect_stderr(err):
            mi.main(["--db", self.db, *argv])
        return out.getvalue(), err.getvalue()

    def sql(self, query, params=()):
        conn = sqlite3.connect(self.db)
        try:
            return conn.execute(query, params).fetchall()
        finally:
            conn.close()


class TestChunker(unittest.TestCase):
    """Pure-function chunking contract (no server involved)."""

    def test_heading_split_keeps_heading_with_section(self):
        content = "lead\n\n# One\nbody one\n\n## Two\nbody two\n\n### Three\nx"
        secs = mi.split_sections(content)
        self.assertEqual(4, len(secs))
        self.assertEqual("lead", secs[0])
        self.assertTrue(secs[1].startswith("# One"))
        self.assertTrue(secs[2].startswith("## Two"))
        self.assertTrue(secs[3].startswith("### Three"))
        self.assertIn("body two", secs[2])

    def test_greedy_merge_deterministic_sizes(self):
        secs = ["# S%d\n%s" % (i, "x" * 400) for i in range(10)]
        chunks = mi.chunk_content("\n\n".join(secs))
        self.assertEqual([1219, 1219, 1219, 405],
                         [len(c) for c in chunks])
        for c in chunks:
            self.assertLessEqual(len(c), mi.CHUNK_MAX)

    def test_merge_never_exceeds_max_when_sections_fit(self):
        secs = ["# S%d\n%s" % (i, "y" * 3000) for i in range(3)]
        chunks = mi.chunk_content("\n\n".join(secs))
        self.assertEqual([3005, 3005, 3005], [len(c) for c in chunks])
        self.assertTrue(all(len(c) <= mi.CHUNK_MAX for c in chunks),
                        "no chunk may exceed CHUNK_MAX=5000")


class TestChunkerEdgeCases(unittest.TestCase):
    def test_oversize_single_section_accepted_whole(self):
        big = "# Big\n" + "y" * 6000
        chunks = mi.chunk_content(big + "\n\n# Small\nzzz")
        self.assertEqual([6006, 11], [len(c) for c in chunks])
        self.assertEqual(big, chunks[0],
                         "oversize section must stay its own intact chunk")

    def test_never_breaks_inside_code_fences(self):
        pre = "# Section A\n" + ("alpha text. " * 58)
        mid = "# Section B\n" + "```\n" + ("code stuff. " * 62)
        content = (pre + "\n\n" + mid
                   + "\n# comment inside fence\nmore code\n```\n\n"
                   + "# Section C\n" + ("omega text. " * 50))
        chunks = mi.chunk_content(content)
        for c in chunks:
            self.assertEqual(
                0, c.count("```") % 2,
                "unbalanced ``` fence: chunk boundary split a code fence")
        joined = "\n\n".join(chunks)
        fence = "```\n" + ("code stuff. " * 62).rstrip() \
            + "\n# comment inside fence\nmore code\n```"
        self.assertIn(fence, joined)

    def test_fences_intact_when_no_heading_like_lines_inside(self):
        body = "## Params\n```\nplain code line\n```\n" + "p" * 300
        content = "# A\n" + body + "\n\n# B\n" + body
        chunks = mi.chunk_content(content)
        for c in chunks:
            self.assertEqual(0, c.count("```") % 2)


class TestSchemaIndexing(IndexerCase):
    """Schema creation + meta dimension probe + basic ingest."""

    def setUp(self):
        super().setUp()
        self.slice = write_slice(self.tmp, "paint.jsonl", [APPLE, ORANGE])
        self.out, self.err = self.cli("add-file", self.slice)

    def test_schema_created(self):
        names = {r[0] for r in self.sql(
            "SELECT name FROM sqlite_master WHERE type IN ('table','trigger')")}
        for want in ("meta", "files", "entries", "chunks", "entries_fts",
                     "entries_ai", "entries_ad", "entries_au"):
            self.assertIn(want, names)
        self.assertEqual("1", self.sql(
            "SELECT value FROM meta WHERE key='schema_version'")[0][0])

    def test_dimension_probe_recorded(self):
        self.assertEqual("stub-embed", self.sql(
            "SELECT value FROM meta WHERE key='embedding_model'")[0][0])
        self.assertEqual(str(DIM), self.sql(
            "SELECT value FROM meta WHERE key='dimension'")[0][0])
        self.assertEqual(["test"], self.stub.calls[0].get("input"),
                         "first embed call must be the dimension probe")

    def test_every_request_pinned_encoding_format_float(self):
        self.assertEqual([], self.stub.bad_bodies)
        self.assertGreater(self.stub.n_calls, 1)
        for body in self.stub.calls:
            self.assertEqual("float", body.get("encoding_format"))


class TestSearchTiers(IndexerCase):
    """add-file lands entries; keyword tiers are embed-free; vector tier
    answers a keyword-missing query."""

    def setUp(self):
        super().setUp()
        self.slice = write_slice(self.tmp, "paint.jsonl", [APPLE, ORANGE])
        self.cli("add-file", self.slice)

    def test_entries_and_chunks_land_embedded(self):
        paths = [r[0] for r in self.sql("SELECT path FROM entries ORDER BY path")]
        self.assertEqual(["paint/brush-apple", "paint/pot-orange"], paths)
        rows = self.sql("SELECT length(embedding) FROM chunks")
        self.assertEqual(2, len(rows))
        for (n,) in rows:
            self.assertEqual(DIM * 4, n, "packed f32 blob of the probed dim")
        fams = self.sql("SELECT family FROM files")
        self.assertEqual([("paint",)], fams)

    def test_fts_hit_never_calls_embed_stub(self):
        before = self.stub.n_calls
        out, _ = self.cli("search", "orchard")
        self.assertIn("paint/brush-apple", out)
        self.assertEqual(before, self.stub.n_calls,
                         "FTS-tier hit must not touch the embed endpoint")
        out, _ = self.cli("search", "orchard", "--json")
        self.assertEqual("fts", json.loads(out)["mode"])
        self.assertEqual(before, self.stub.n_calls)

    def test_command_tier_never_calls_embed_stub(self):
        before = self.stub.n_calls
        out, _ = self.cli("search", "brush-apple")
        self.assertIn("paint/brush-apple", out)
        self.assertEqual(before, self.stub.n_calls,
                         "command-tier hit must not touch the embed endpoint")

    def test_vector_search_finds_semantic_miss(self):
        before = self.stub.n_calls
        out, _ = self.cli("search", "zingyfruit harvest", "--json")
        payload = json.loads(out)
        self.assertEqual("vector", payload["mode"])
        self.assertGreater(self.stub.n_calls, before,
                           "vector tier must embed the query")
        hits = payload["results"]
        self.assertTrue(hits, "expected at least one vector hit")
        self.assertEqual("paint/brush-apple", hits[0]["path"])
        self.assertGreater(hits[0]["score"], 0.9,
                           "stub vectors put brush-apple closest to the query")


class TestUpsertAndRemove(IndexerCase):
    def test_readd_unchanged_embeds_nothing(self):
        sl = write_slice(self.tmp, "paint.jsonl", [APPLE])
        self.cli("add-file", sl)
        after_first = self.stub.n_calls
        out, _ = self.cli("add-file", sl)
        self.assertIn("unchanged", out)
        self.assertEqual(after_first, self.stub.n_calls,
                         "identical sha256 must skip embedding entirely")
        self.assertEqual(1, self.sql("SELECT count(*) FROM entries")[0][0])

    def test_changed_content_replaces_old_entry(self):
        sl = write_slice(self.tmp, "paint.jsonl", [APPLE])
        self.cli("add-file", sl)
        apple2 = dict(APPLE, oneliner="Repaint the golden apple vat")
        sl2 = write_slice(self.tmp, "paint.jsonl", [apple2])
        out, _ = self.cli("add-file", sl2)
        self.assertIn("ingested 1", out)
        rows = self.sql("SELECT oneliner FROM entries WHERE path=?",
                        ("paint/brush-apple",))
        self.assertEqual(1, len(rows))
        self.assertEqual("Repaint the golden apple vat", rows[0][0])
        self.assertEqual(1, self.sql("SELECT count(*) FROM files")[0][0])
        self.assertEqual(1, self.sql("SELECT count(*) FROM chunks")[0][0],
                         "old chunks must be replaced, not appended")
        out, _ = self.cli("search", "golden", "--json")
        self.assertEqual("paint/brush-apple",
                         json.loads(out)["results"][0]["path"])

    def test_remove_file_deletes(self):
        both = write_slice(self.tmp, "both.jsonl", [APPLE, ORANGE])
        self.cli("add-file", both)
        out, _ = self.cli("remove-file", "paint/")
        self.assertIn("removed 2", out)
        self.assertEqual(0, self.sql("SELECT count(*) FROM entries")[0][0])
        self.assertEqual(0, self.sql("SELECT count(*) FROM chunks")[0][0])
        out, _ = self.cli("search", "orchard")
        self.assertIn("(no results)", out)

    def test_readd_after_remove_reingests(self):
        both = write_slice(self.tmp, "both.jsonl", [APPLE])
        self.cli("add-file", both)
        self.cli("remove-file", "paint/")
        out, _ = self.cli("add-file", both)
        self.assertIn("ingested", out)
        self.assertEqual(1, self.sql("SELECT count(*) FROM entries")[0][0])


class TestExport(IndexerCase):
    def test_export_family_files_deterministic(self):
        sl = write_slice(self.tmp, "all.jsonl", [APPLE, ORANGE, GLAZE])
        self.cli("add-file", sl)
        outdir = os.path.join(self.tmp, "export")
        self.cli("export", "--dir", outdir)
        paint = os.path.join(outdir, "paint.md")
        glaze = os.path.join(outdir, "glaze.md")
        self.assertTrue(os.path.isfile(paint), "paint.md must be generated")
        self.assertTrue(os.path.isfile(glaze), "glaze.md must be generated")
        with open(paint, encoding="utf-8") as fh:
            text = fh.read()
        self.assertTrue(text.startswith("# paint\n"))
        index_lines = [l for l in text.splitlines() if l.startswith("- `")]
        self.assertEqual(["- `brush-apple` — Paint an apple orchard slice",
                          "- `pot-orange` — Shape a citrus orange pot"],
                         index_lines, "index ordered by sort_order, command")
        self.assertIn("search \"<command>\"", text,
                      "index-only export must teach CLI retrieval")
        self.assertNotIn("## brush-apple", text,
                         "export is an index; detail cards live in the DB")
        def snapshot():
            snap = {}
            for f in sorted(os.listdir(outdir)):
                with open(os.path.join(outdir, f), "rb") as fh:
                    snap[f] = fh.read()
            return snap
        first = snapshot()
        self.cli("export", "--dir", outdir)
        second = snapshot()
        self.assertEqual(first, second, "export must be deterministic")


class TestEmbedGatewayFlake(unittest.TestCase):
    """Real subprocess runs: authentic exit codes/stderr. The indexer script
    runs with PHOTOCRAFT_ART_DIRECTOR_HOME pointed at the tmpdir so the
    stub config.json is read; the real machine-local config is never read
    or modified."""

    def _run(self, behavior):
        tmp = tempfile.mkdtemp(prefix="mi-flake-")
        self.addCleanup(shutil.rmtree, tmp, True)
        stub = StubEmbedServer(behavior)
        self.addCleanup(stub.close)
        script = os.path.join(tmp, "mind_index.py")
        shutil.copy(MIND_INDEX, script)
        with open(os.path.join(tmp, "config.json"), "w",
                  encoding="utf-8") as fh:
            json.dump({"base_url": stub.url, "model": "stub-embed",
                       "api_key": "k", "timeout_s": 10}, fh)
        sl = write_slice(tmp, "paint.jsonl", [APPLE])
        env = dict(os.environ,
                   PHOTOCRAFT_ART_DIRECTOR_HOME=tmp)
        proc = subprocess.run(
            [sys.executable, script, "--db", os.path.join(tmp, "i.sqlite"),
             "add-file", sl], capture_output=True, text=True, timeout=60,
            env=env)
        return proc, stub, tmp

    def test_403_twice_then_200_still_succeeds(self):
        proc, stub, _tmp = self._run("flake2")
        self.assertEqual(0, proc.returncode, proc.stderr[-400:])
        self.assertGreaterEqual(stub.n_calls, 3, "two 403s then a 200")
        self.assertIn("ingested", proc.stdout)

    def test_always_403_leaves_keyword_only_exit_0(self):
        proc, stub, tmp = self._run("always403")
        self.assertEqual(0, proc.returncode, proc.stderr[-400:])
        self.assertIn("keyword-only", proc.stderr.lower())
        conn = sqlite3.connect(os.path.join(tmp, "i.sqlite"))
        try:
            n = conn.execute("SELECT count(*) FROM entries").fetchone()[0]
        finally:
            conn.close()
        self.assertEqual(1, n, "slice must still land, unembedded")

    def test_mid_ingest_failure_falls_back_keyword_only(self):
        """The graceful degradation that IS implemented: probe succeeds,
        then the chunk batch 403s -> rows stored unembedded, warning issued,
        exit 0, keyword search keeps working."""
        proc, stub, tmp = self._run("probe_ok_then_403")
        self.assertEqual(0, proc.returncode, proc.stderr[-400:])
        self.assertIn("keyword-only", proc.stderr.lower())
        self.assertIn("embedding failed", proc.stderr)
        self.assertIn("ingested 1", proc.stdout)
        conn = sqlite3.connect(os.path.join(tmp, "i.sqlite"))
        try:
            rows = conn.execute(
                "SELECT embedding IS NULL FROM chunks").fetchall()
            n_entries = conn.execute(
                "SELECT count(*) FROM entries").fetchone()[0]
        finally:
            conn.close()
        self.assertEqual(1, n_entries)
        self.assertEqual([(1,)], rows, "chunks stored without vectors")
        out = subprocess.run(
            [sys.executable, os.path.join(tmp, "mind_index.py"),
             "--db", os.path.join(tmp, "i.sqlite"), "search", "apple"],
            capture_output=True, text=True, timeout=60)
        self.assertEqual(0, out.returncode, out.stderr[-400:])
        self.assertIn("paint/brush-apple", out.stdout)


if __name__ == "__main__":
    unittest.main()
