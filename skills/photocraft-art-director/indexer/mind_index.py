#!/usr/bin/env python3
"""PhotoCraft mind-map RAG indexer.

The sqlite DB is the primary store of the skill's tool mind maps;
the Markdown family files are generated exports.

Subcommands: add-file, remove-file, search, export, rebuild, stats, files.
No third-party runtime deps; `sqlite-vec` support via try-import.
Config (indexer/config.json, gitignored) is read at runtime and never
printed or logged; no config file => keyword-only mode, no crash.
"""

import argparse
import hashlib
import json
import math
import os
import re
import sqlite3
import struct
import sys
import time
import urllib.error
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB = os.path.join(SCRIPT_DIR, "index.sqlite")
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")
DEFAULT_EXPORT_DIR = os.path.normpath(
    os.path.join(SCRIPT_DIR, "..", "references", "mindmaps"))

SCHEMA_VERSION = "1"

CHUNK_MIN = 500
CHUNK_PREF = 1500
CHUNK_MAX = 5000
EXPORT_WARN_LINES = 300

try:
    import sqlite_vec
    HAS_SQLITE_VEC = True
except Exception:
    sqlite_vec = None
    HAS_SQLITE_VEC = False


class EmbedError(Exception):
    pass


# ---------------------------------------------------------------- config

class Config:
    """Embed endpoint config. Contents are never printed or logged."""

    def __init__(self, data):
        self.base_url = str(data["base_url"]).rstrip("/")
        self.model = str(data["model"])
        self.api_key = str(data.get("api_key", ""))
        self.timeout_s = float(data.get("timeout_s", 60))
        self.batch_size = int(data.get("batch_size", 100))
        self.batch_chars = int(data.get("batch_chars", 50000))


def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
            return Config(json.load(fh))
    except FileNotFoundError:
        return None
    except Exception as exc:
        sys.stderr.write(
            f"warning: config.json unreadable ({exc.__class__.__name__}); "
            "running keyword-only\n")
        return None


# ---------------------------------------------------------------- schema

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS meta(
  key TEXT PRIMARY KEY,
  value TEXT
);
CREATE TABLE IF NOT EXISTS files(
  id INTEGER PRIMARY KEY,
  path TEXT UNIQUE,
  sha256 TEXT,
  mtime REAL,
  family TEXT
);
CREATE TABLE IF NOT EXISTS entries(
  id INTEGER PRIMARY KEY,
  path TEXT UNIQUE,
  family TEXT,
  command TEXT,
  title TEXT,
  oneliner TEXT,
  content TEXT,
  keywords TEXT,
  sort_order INTEGER
);
CREATE TABLE IF NOT EXISTS chunks(
  id INTEGER PRIMARY KEY,
  entry_id INTEGER REFERENCES entries(id) ON DELETE CASCADE,
  content TEXT,
  embedding BLOB
);
CREATE VIRTUAL TABLE IF NOT EXISTS entries_fts USING fts5(
  content, title, keywords,
  content='entries',
  content_rowid='id',
  tokenize='porter unicode61'
);
CREATE TRIGGER IF NOT EXISTS entries_ai AFTER INSERT ON entries BEGIN
  INSERT INTO entries_fts(rowid, content, title, keywords)
    VALUES (new.id, new.content, new.title, new.keywords);
END;
CREATE TRIGGER IF NOT EXISTS entries_ad AFTER DELETE ON entries BEGIN
  INSERT INTO entries_fts(entries_fts, rowid, content, title, keywords)
    VALUES ('delete', old.id, old.content, old.title, old.Keywords);
END;
CREATE TRIGGER IF NOT EXISTS entries_au AFTER UPDATE ON entries BEGIN
  INSERT INTO entries_fts(entries_fts, rowid, content, title, keywords)
    VALUES ('delete', old.id, old.content, old.title, old.Keywords);
  INSERT INTO entries_fts(rowid, content, title, keywords)
    VALUES (new.id, new.content, new.title, new.keywords);
END;
"""


def open_db(path):
    conn = sqlite3.connect(path, timeout=120)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_SQL)
    if HAS_SQLITE_VEC:
        try:
            conn.enable_load_extension(True)
            sqlite_vec.load(conn)
        except Exception:
            pass
    return conn


def meta_get(conn, key):
    row = conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    return row["value"] if row else None


def meta_set(conn, key, value):
    conn.execute(
        "INSERT INTO meta(key,value) VALUES(?,?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, str(value)))


def ensure_meta(conn):
    if meta_get(conn, "schema_version") is None:
        meta_set(conn, "schema_version", SCHEMA_VERSION)


def get_dimension(conn):
    val = meta_get(conn, "dimension")
    return int(val) if val else None


def require_model_compat(conn, cfg):
    """Return stored dimension, or None if never embedded. Refuse to proceed
    if the stored model/dimension conflicts with the current config."""
    stored_model = meta_get(conn, "embedding_model")
    stored_dim = get_dimension(conn)
    if stored_model is None:
        return None
    if cfg is None or cfg.model != stored_model:
        raise SystemExit(
            f"error: index was embedded with model '{stored_model}'"
            f" (dimension {stored_dim}), which does not match the current "
            "config (or config is absent). Run `rebuild` to re-embed, or "
            "use keyword search without a config.")
    return stored_dim


def vec_available(conn):
    return HAS_SQLITE_VEC and conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name='chunks_vec'").fetchone() is not None


def setup_vec_table(conn, dim):
    if HAS_SQLITE_VEC and dim and not vec_available(conn):
        try:
            conn.execute(
                f"CREATE VIRTUAL TABLE chunks_vec USING vec0(embedding FLOAT[{dim}])")
        except sqlite3.Error as exc:
            sys.stderr.write(f"warning: sqlite-vec init failed: {exc}\n")


def provision_embedding(conn, cfg):
    """Resolve the stored dimension, embedding a probe on first use."""
    stored_dim = require_model_compat(conn, cfg)
    if stored_dim is None:
        if cfg is None:
            return None
        stored_dim = probe_dimension(cfg)
        meta_set(conn, "embedding_model", cfg.model)
        meta_set(conn, "dimension", str(stored_dim))
        setup_vec_table(conn, stored_dim)
    return stored_dim


# ---------------------------------------------------------------- embedding

def _embed_once(cfg, texts):
    body = json.dumps(
        {"model": cfg.model, "input": texts, "encoding_format": "float"}
    ).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if cfg.api_key:
        headers["Authorization"] = f"Bearer {cfg.api_key}"
    req = urllib.request.Request(
        f"{cfg.base_url}/embeddings", data=body, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=cfg.timeout_s) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", "replace")[:300]
        except Exception:
            pass
        raise EmbedError(f"HTTP {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise EmbedError(f"transport: {exc}") from exc
    data = payload.get("data")
    if not isinstance(data, list) or len(data) != len(texts):
        raise EmbedError("malformed embedding response")
    data = sorted(data, key=lambda d: d.get("index", 0))
    return [item["embedding"] for item in data]


def _embed_with_retries(cfg, texts):
    """Retry transient failures up to 3 total tries (2s/8s backoff):
    transport errors, HTTP 4xx (flaky auth, rate limits) and 5xx.
    Payload-size errors raise immediately — batch halving handles them."""
    delays = [2, 8]
    attempt = 0
    while True:
        try:
            return _embed_once(cfg, texts)
        except EmbedError as exc:
            if _is_size_error(exc):
                raise
            if attempt >= len(delays):
                raise
            time.sleep(delays[attempt])
            attempt += 1
            continue


def _is_size_error(err):
    msg = str(err)
    if not (msg.startswith("HTTP 400") or msg.startswith("HTTP 413")):
        return False
    low = msg.lower()
    return any(w in low for w in (
        "size", "length", "too large", "too long", "limit", "exceed",
        "payload", "token", "context"))


def _embed_size_aware(cfg, texts):
    """Halve the batch recursively on input-size HTTP errors; a single
    oversized text is truncated to half once."""
    try:
        return _embed_with_retries(cfg, texts)
    except EmbedError as exc:
        if not _is_size_error(exc):
            raise
    if len(texts) > 1:
        mid = len(texts) // 2
        return (_embed_size_aware(cfg, texts[:mid])
                + _embed_size_aware(cfg, texts[mid:]))
    truncated = texts[0][: max(1, len(texts[0]) // 2)]
    return _embed_no_auth_retry(cfg, [truncated])


def embed_texts(cfg, texts):
    """Embed texts, honoring BOTH batch_size (count) and batch_chars."""
    out = []
    i = 0
    while i < len(texts):
        batch = []
        chars = 0
        while i < len(texts) and len(batch) < cfg.batch_size:
            t = texts[i]
            if batch and chars + len(t) > cfg.batch_chars:
                break
            batch.append(t)
            chars += len(t)
            i += 1
        out.extend(_embed_size_aware(cfg, batch))
    return out


def probe_dimension(cfg):
    return len(embed_texts(cfg, ["test"])[0])


def pack_f32(vec):
    return struct.pack("<%df" % len(vec), *vec)


def unpack_f32(blob):
    return list(struct.unpack("<%df" % (len(blob) // 4), blob))


def pad_to(vec, dim):
    """Zero-pad shorter vectors to the stored dimension; never truncate."""
    if dim and len(vec) < dim:
        return vec + [0.0] * (dim - len(vec))
    return vec


# ---------------------------------------------------------------- chunking

HEADING_RE = re.compile(r"^#{1,4} ", re.M)


def split_sections(content):
    """Split on markdown headings; the heading line stays with its section.
    Fence-aware: ``` fences open/close state is tracked line-by-line, and
    heading detection is suspended inside a fence (column-0 lines like
    `# comment` inside a code block are NOT headings)."""
    if not content.strip():
        return []
    fence_open = False
    boundaries = [0]  # byte offsets (char offsets) where a new section starts
    pos = 0
    for line in content.splitlines(keepends=True):
        stripped = line.rstrip("\r\n")
        if stripped.startswith("```"):
            fence_open = not fence_open
        elif not fence_open and HEADING_RE.match(line):
            # A heading starts a new section, but the very first line of the
            # content is not a 'boundary' (the preamble section would be
            # empty and is dropped later anyway); still record it.
            boundaries.append(pos)
        pos += len(line)
    boundaries = sorted(set(boundaries))
    if len(boundaries) == 1 and boundaries[0] == 0:
        return [content.strip()]
    sections = []
    for i, start in enumerate(boundaries):
        end = boundaries[i + 1] if i + 1 < len(boundaries) else len(content)
        piece = content[start:end].strip()
        if piece:
            sections.append(piece)
    return sections


def chunk_content(content):
    """Split on markdown headings, then greedy-merge the heading sections:
    chunks aim for >= CHUNK_MIN (min 500), preferably <= CHUNK_PREF
    (preferred 1500), and never exceed CHUNK_MAX (max 5000) unless a single
    heading section is itself larger — that section becomes its own
    oversize chunk (spec: accept oversize instead of splitting). Fences:
    `split_sections` tracks ``` state line-by-line, so heading-shaped
    lines inside a code fence never start a section and no chunk boundary
    can fall inside a fence. Emitted chunks are normalized with trailing
    whitespace stripped per line (`textify_chunk`)."""
    chunks = []
    buf = ""
    for sec in split_sections(content):
        if not buf:
            buf = sec
        elif len(sec) > CHUNK_MAX or len(buf) + 2 + len(sec) > CHUNK_MAX:
            chunks.append(buf)
            buf = sec
        elif len(buf) + 2 + len(sec) <= CHUNK_PREF:
            buf = f"{buf}\n\n{sec}"
        elif len(buf) >= CHUNK_MIN:
            chunks.append(buf)
            buf = sec
        else:
            buf = f"{buf}\n\n{sec}"
    if buf:
        chunks.append(buf)
    return [textify_chunk(c) for c in chunks]


def textify_chunk(chunk):
    """Normalize a chunk's text: strip every line's trailing whitespace.
    Chunk text feeds embeddings and (re-joined) inspection only; the
    authoritative text for FTS/export stays in `entries.content`."""
    return "\n".join(line.rstrip() for line in chunk.split("\n"))


def embed_text_for(title, path, chunk):
    return f"<title>{title}</title>\n<path>{path}</path>\n{chunk}"


# ---------------------------------------------------------------- ingest

REQUIRED_FIELDS = ("path", "family", "command", "title", "oneliner")


def entry_content(rec):
    """Searchable text: title + oneliner + params_md + traps_md + intents +
    keywords joined."""
    parts = [rec.get("title", ""), rec.get("oneliner", ""),
             rec.get("params_md", ""), rec.get("traps_md", "")]
    intents = rec.get("intents") or []
    keywords = rec.get("keywords") or []
    if intents:
        parts.append("Intents: " + "; ".join(str(i) for i in intents))
    if keywords:
        parts.append("Keywords: " + ", ".join(str(k) for k in keywords))
    return "\n\n".join(p for p in parts if p)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def read_jsonl(path):
    records = []
    with open(path, "r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{lineno}: invalid JSON: {exc}") from exc
    return records


def delete_path_rows(conn, entry_path):
    """Delete every rows/tuple belonging to one entry path (in-transaction
    caller; chunks+vec rows first, then the entry)."""
    row = conn.execute("SELECT id FROM entries WHERE path=?", (entry_path,)).fetchone()
    if not row:
        return
    eid = row["id"]
    if vec_available(conn):
        conn.execute(
            "DELETE FROM chunks_vec WHERE rowid IN "
            "(SELECT id FROM chunks WHERE entry_id=?)", (eid,))
    conn.execute("DELETE FROM chunks WHERE entry_id=?", (eid,))
    conn.execute("DELETE FROM entries WHERE id=?", (eid,))


def validate_records(records, slice_path):
    for i, rec in enumerate(records, 1):
        if not isinstance(rec, dict):
            raise ValueError(f"{slice_path}:{i}: record is not a JSON object")
        for field in REQUIRED_FIELDS:
            if field not in rec:
                raise ValueError(f"{slice_path}:{i}: missing field '{field}'")


def upsert_slice(conn, slice_path, records, cfg, stored_dim):
    """add/update for a slice: delete all rows for each record's path, then
    re-insert (with its chunks), plus the files row — in one transaction."""
    digest = sha256_file(slice_path)
    mtime = os.path.getmtime(slice_path)
    family = records[0]["family"] if records else ""
    pending_chunks = []
    for rec in records:
        entry_path = rec["path"]
        content = entry_content(rec)
        keywords = " ".join(str(k) for k in (rec.get("keywords") or []))
        order = int(rec.get("order", 0))
        delete_path_rows(conn, entry_path)
        cur = conn.execute(
            "INSERT INTO entries(path,family,command,title,oneliner,content,"
            "keywords,sort_order) VALUES(?,?,?,?,?,?,?,?)",
            (entry_path, rec["family"], rec["command"], rec["title"],
             rec["oneliner"], content, keywords, order))
        entry_id = cur.lastrowid
        chunks = chunk_content(content)
        if stored_dim:
            texts = [embed_text_for(rec["title"], entry_path, c) for c in chunks]
            try:
                vecs = embed_texts(cfg, texts)
            except EmbedError as exc:
                # Keyword path must stay usable if the embed endpoint dies
                # mid-ingest: keep the rows, store chunks without vectors,
                # warn once, and mark meta so search does not try vectors.
                sys.stderr.write(
                    f"warning: embedding failed for '{entry_path}' "
                    f"({exc}); storing chunks without vectors\n")
                sys.stderr.write(
                    "warning: index is now keyword-only for the new rows; "
                    "re-run `add-file --force` (or `rebuild`) once the "
                    "endpoint is back\n")
                if not meta_get(conn, "embedding_model"):
                    meta_set(conn, "embedding_model", cfg.model)
                meta_set(conn, "dimension", "")
                stored_dim = None
                cfg = None
            else:
                for chunk, vec in zip(chunks, vecs):
                    vec = pad_to([float(x) for x in vec], stored_dim)
                    pending_chunks.append((entry_id, chunk, pack_f32(vec)))
                continue
        if not stored_dim:
            for chunk in chunks:
                pending_chunks.append((entry_id, chunk, None))
    with conn:
        conn.execute(
            "INSERT INTO files(path,sha256,mtime,family) VALUES(?,?,?,?) "
            "ON CONFLICT(path) DO UPDATE SET sha256=excluded.sha256,"
            "mtime=excluded.mtime,family=excluded.family",
            (slice_path, digest, mtime, family))
        for entry_id, chunk, blob in pending_chunks:
            cur = conn.execute(
                "INSERT INTO chunks(entry_id,content,embedding) VALUES(?,?,?)",
                (entry_id, chunk, blob))
            if blob is not None and vec_available(conn):
                conn.execute(
                    "INSERT INTO chunks_vec(rowid, embedding) VALUES(?,?)",
                    (cur.lastrowid, blob))


def cmd_add_file(conn, args, cfg):
    slice_path = os.path.abspath(args.slice)
    if not os.path.isfile(slice_path):
        raise SystemExit(f"error: no such file: {slice_path}")
    digest = sha256_file(slice_path)
    row = conn.execute("SELECT sha256 FROM files WHERE path=?", (slice_path,)).fetchone()
    if row and row["sha256"] == digest and not args.force:
        print(f"unchanged: {slice_path} (skipped; use --force to re-embed)")
        return
    records = read_jsonl(slice_path)
    validate_records(records, slice_path)
    cfg_effective = cfg if cfg else (load_config() if get_dimension(conn) else None)
    stored_dim = None
    if cfg_effective:
        try:
            stored_dim = provision_embedding(conn, cfg_effective)
        except EmbedError as exc:
            sys.stderr.write(
                f"warning: embedding failed at the dimension probe ({exc}); "
                "storing slice keyword-only\n")
            sys.stderr.write(
                "warning: index is now keyword-only for the new rows; "
                "re-run `add-file --force` (or `rebuild`) once the "
                "endpoint is back\n")
            if not meta_get(conn, "embedding_model"):
                meta_set(conn, "embedding_model", cfg_effective.model)
            meta_set(conn, "dimension", "")
            stored_dim = None
            cfg_effective = None
    else:
        stored_dim = get_dimension(conn)
    upsert_slice(conn, slice_path, records, cfg_effective, stored_dim)
    print(f"ingested {len(records)} record(s) from {slice_path}")


def cmd_remove_file(conn, args):
    like = args.prefix + "%"
    n = conn.execute(
        "SELECT count(*) AS c FROM entries WHERE path LIKE ?", (like,)).fetchone()["c"]
    with conn:
        if vec_available(conn):
            conn.execute(
                "DELETE FROM chunks_vec WHERE rowid IN "
                "(SELECT c.id FROM chunks c JOIN entries e ON c.entry_id=e.id "
                "WHERE e.path LIKE ?)", (like,))
        # Find every entry row being removed; note which slice files they
        # came from so the files row is also removed (D4).
        affected = conn.execute(
            "SELECT DISTINCT family FROM entries WHERE path LIKE ?",
            (like,)).fetchall()
        conn.execute(
            "DELETE FROM chunks WHERE entry_id IN "
            "(SELECT id FROM entries WHERE path LIKE ?)", (like,))
        conn.execute("DELETE FROM entries WHERE path LIKE ?", (like,))
        # Remove files rows whose family exactly matches a de-prefixed
        # family (a path prefix like "paint/" corresponds to family
        # "paint") and whose entries are now all gone; also remove files
        # rows whose path literally matches the prefix (absolute paths).
        for fam_row in affected:
            fam = fam_row["family"]
            if not fam:
                continue
            remaining = conn.execute(
                "SELECT count(*) AS c FROM entries WHERE family=?",
                (fam,)).fetchone()["c"]
            if remaining == 0:
                conn.execute("DELETE FROM files WHERE family=?", (fam,))
        conn.execute("DELETE FROM files WHERE path LIKE ?", (like,))
    print(f"removed {n} entr{'y' if n == 1 else 'ies'} matching '{args.prefix}*'")


# ---------------------------------------------------------------- search

def fts_query_string(query):
    parts = re.findall(r"\"([^\"]+)\"|(\S+)", query)
    terms = [m[0] or m[1] for m in parts]
    terms = [t for t in terms if t]
    if not terms:
        return None
    return " OR ".join(f'"{t.replace(chr(34), chr(34) * 2)}"' for t in terms)


def search_command(conn, query, limit):
    q = query.strip()
    exact = conn.execute(
        "SELECT path,family,command,title,oneliner,keywords,sort_order "
        "FROM entries WHERE command=? OR path=? "
        "ORDER BY sort_order, command LIMIT ?", (q, q, limit)).fetchall()
    if len(exact) >= limit:
        return exact
    prefix = conn.execute(
        "SELECT path,family,command,title,oneliner,keywords,sort_order "
        "FROM entries WHERE (command LIKE ? ESCAPE '\\' OR path LIKE ? ESCAPE '\\') "
        "AND command != ? AND path != ? "
        "ORDER BY length(command), sort_order LIMIT ?",
        (_like_escape(q) + "%", _like_escape(q) + "%", q, q,
         limit - len(exact))).fetchall()
    return list(exact) + list(prefix)


def _like_escape(s):
    return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def search_fts(conn, query, limit):
    ftsq = fts_query_string(query)
    if not ftsq:
        return []
    try:
        return conn.execute(
            "SELECT e.path,e.family,e.command,e.title,e.oneliner,e.keywords,"
            "e.sort_order FROM entries_fts "
            "JOIN entries e ON e.id = entries_fts.rowid "
            "WHERE entries_fts MATCH ? ORDER BY bm25(entries_fts) LIMIT ?",
            (ftsq, limit)).fetchall()
    except sqlite3.Error:
        return []


def cosine(a, b):
    num = sum(x * y for x, y in zip(a, b))
    da = math.sqrt(sum(x * x for x in a))
    db = math.sqrt(sum(x * x for x in b))
    return num / (da * db) if da and db else 0.0


def search_vector(conn, cfg, query, limit, stored_dim):
    qvec = embed_texts(cfg, [embed_text_for(query, "query", query)])[0]
    qvec = pad_to([float(x) for x in qvec], stored_dim)
    if vec_available(conn):
        rows = conn.execute(
            "SELECT rowid, distance FROM chunks_vec "
            "WHERE embedding MATCH ? AND k=?", (pack_f32(qvec), limit)).fetchall()
        results = []
        for r in rows:
            chunk = conn.execute(
                "SELECT entry_id FROM chunks WHERE id=?", (r["rowid"],)).fetchone()
            if not chunk:
                continue
            e = conn.execute(
                "SELECT path,family,command,title,oneliner,keywords,sort_order "
                "FROM entries WHERE id=?", (chunk["entry_id"],)).fetchone()
            if e:
                d = dict(e)
                d["score"] = 1.0 / (1.0 + r["distance"])
                results.append(d)
        return results
    best = {}
    for row in conn.execute(
            "SELECT entry_id, embedding FROM chunks WHERE embedding IS NOT NULL"):
        score = cosine(qvec, unpack_f32(row["embedding"]))
        eid = row["entry_id"]
        if eid not in best or score > best[eid]:
            best[eid] = score
    results = []
    for eid, score in sorted(best.items(), key=lambda kv: -kv[1])[:limit]:
        e = conn.execute(
            "SELECT path,family,command,title,oneliner,keywords,sort_order "
            "FROM entries WHERE id=?", (eid,)).fetchone()
        if e:
            d = dict(e)
            d["score"] = score
            results.append(d)
    return results


def cmd_search(conn, args, cfg):
    limit = max(1, args.limit)
    mode = "command"
    hits = search_command(conn, args.query, limit)
    if not hits:
        mode = "fts"
        hits = search_fts(conn, args.query, limit)
    if not hits and cfg is not None:
        stored_dim = require_model_compat(conn, cfg)
        if stored_dim:
            mode = "vector"
            hits = search_vector(conn, cfg, args.query, limit, stored_dim)
    if args.json:
        print(json.dumps({"mode": mode, "query": args.query,
                          "results": [dict(h) for h in hits]}, indent=2))
        return
    if not hits:
        print("(no results)")
        return
    for h in hits:
        extra = f" | score:{h['score']:.4f}" if "score" in h else ""
        print(f"{h['path']} | {h['title']} | {h['oneliner']}{extra}")


# ---------------------------------------------------------------- export

def family_markdown(conn, family):
    rows = conn.execute(
        "SELECT command,title,oneliner,content,sort_order "
        "FROM entries WHERE family=? ORDER BY sort_order, command",
        (family,)).fetchall()
    lines = [f"# {family}", ""]
    for r in rows:
        lines.append(f"- `{r['command']}` — {r['oneliner']}")
    lines += [
        "",
        "Full params, traps, and evidence for each command live in the "
        "search index:",
        "`python3 indexer/mind_index.py search \"<command>\"`",
    ]
    return "\n".join(lines).rstrip() + "\n"


def cmd_export(conn, args):
    out_dir = os.path.abspath(args.dir)
    os.makedirs(out_dir, exist_ok=True)
    families = [r["family"] for r in conn.execute(
        "SELECT DISTINCT family FROM entries ORDER BY family")]
    for family in families:
        text = family_markdown(conn, family)
        out_path = os.path.join(out_dir, f"{family}.md")
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(text)
        n_lines = text.count("\n")
        if n_lines > EXPORT_WARN_LINES:
            sys.stderr.write(
                f"warning: {family}.md exceeds {EXPORT_WARN_LINES} lines "
                f"({n_lines})\n")
        print(f"wrote {out_path} ({n_lines} lines)")
    if not families:
        print("(index empty; nothing to export)")


# ---------------------------------------------------------------- rebuild

def _wipe_index(conn):
    with conn:
        if vec_available(conn):
            conn.execute("DELETE FROM chunks_vec")
        conn.execute("DELETE FROM chunks")
        conn.execute("DELETE FROM entries")
        conn.execute("DELETE FROM files")
        conn.execute(
            "DELETE FROM meta WHERE key IN ('embedding_model','dimension')")


def cmd_rebuild(conn, args, cfg):
    """Drop all entry/chunk/files data (schema and meta other than the
    embedding identity survive) and re-ingest every .jsonl slice under
    <slice_dir>, add-file semantics per file."""
    slice_dir = os.path.abspath(args.slice_dir)
    if not os.path.isdir(slice_dir):
        raise SystemExit(f"error: not a directory: {slice_dir}")
    _wipe_index(conn)
    names = sorted(os.path.relpath(os.path.join(root, n), slice_dir)
                   for root, _dirs, files in os.walk(slice_dir)
                   for n in files if n.endswith(".jsonl"))
    total = 0
    usable = 0
    for rel in sorted(set(names)):
        slice_path = os.path.join(slice_dir, rel)
        try:
            records = read_jsonl(slice_path)
            validate_records(records, slice_path)
        except (ValueError, OSError) as exc:
            sys.stderr.write(f"warning: skipping {rel}: {exc}\n")
            continue
        cfg_effective = cfg if cfg else (load_config() if get_dimension(conn) else None)
        stored_dim = (provision_embedding(conn, cfg_effective) if cfg_effective
                      else get_dimension(conn))
        upsert_slice(conn, slice_path, records, cfg_effective, stored_dim)
        total += len(records)
        usable += 1
        print(f"ingested {len(records)} record(s) from {slice_path}")
    print(f"rebuild complete: {total} record(s) from {usable} file(s)")


# ---------------------------------------------------------------- stats/files

def cmd_stats(conn, cfg):
    db_path = conn.execute("PRAGMA database_list").fetchone()[2]
    entries = conn.execute("SELECT count(*) AS c FROM entries").fetchone()["c"]
    chunks = conn.execute("SELECT count(*) AS c FROM chunks").fetchone()["c"]
    model = meta_get(conn, "embedding_model") or "(none)"
    dim = get_dimension(conn) or "(none)"
    mode = "embed-ready" if cfg else "keyword-only"
    if cfg and meta_get(conn, "embedding_model") is None:
        mode += " (no embeddings yet)"
    vec = ("sqlite-vec" if HAS_SQLITE_VEC
           else "brute-force cosine (sqlite-vec absent)")
    print(f"db: {db_path}")
    print(f"schema_version: {meta_get(conn, 'schema_version') or '(unset)'}")
    print(f"mode: {mode}; vector engine: {vec}")
    print(f"embedding_model: {model}")
    print(f"dimension: {dim}")
    print(f"entries: {entries}")
    print(f"chunks: {chunks}")
    for r in conn.execute(
        "SELECT family, count(*) AS c FROM entries GROUP BY family "
        "ORDER BY family"):
        print(f"  {r['family']}: {r['c']} entries")


def cmd_files(conn):
    rows = conn.execute(
        "SELECT path,sha256,mtime,family FROM files ORDER BY path").fetchall()
    if not rows:
        print("(no slice files recorded)")
        return
    for r in rows:
        ts = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(r["mtime"] or 0))
        short = (r["sha256"] or "")[:12]
        print(f"{r['path']}  sha256:{short}  mtime:{ts}  family:{r['family'] or ''}")


# ---------------------------------------------------------------- main

def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="mind_index",
        description="PhotoCraft mind-map RAG indexer (sqlite primary store).")
    parser.add_argument("--db", default=DEFAULT_DB,
                        help="sqlite index path (default: <script-dir>/index.sqlite)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("add-file", help="upsert a JSONL slice file")
    p.add_argument("slice", help="path to a .jsonl slice")
    p.add_argument("--force", action="store_true",
                   help="re-embed even if the slice sha256 is unchanged")

    p = sub.add_parser("remove-file", help="delete entries by path prefix")
    p.add_argument("prefix")

    p = sub.add_parser("search", help="command/FTS/vector search, in that order")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("export", help="regenerate family markdown from the DB")
    p.add_argument("--dir", default=DEFAULT_EXPORT_DIR)

    p = sub.add_parser("rebuild",
                       help="drop entry data (keep meta) and re-ingest a slice dir")
    p.add_argument("slice_dir")

    sub.add_parser("stats", help="index statistics")
    sub.add_parser("files", help="list ingested slice files")

    args = parser.parse_args(argv)
    cfg = load_config()

    conn = open_db(os.path.abspath(args.db))
    ensure_meta(conn)
    conn.commit()

    if args.cmd == "add-file":
        cmd_add_file(conn, args, cfg)
    elif args.cmd == "remove-file":
        cmd_remove_file(conn, args)
    elif args.cmd == "search":
        cmd_search(conn, args, cfg)
    elif args.cmd == "export":
        cmd_export(conn, args)
    elif args.cmd == "rebuild":
        cmd_rebuild(conn, args, cfg)
    elif args.cmd == "stats":
        cmd_stats(conn, cfg)
    elif args.cmd == "files":
        cmd_files(conn)
    conn.close()


if __name__ == "__main__":
    main()
