#!/usr/bin/env python3
"""Cross-project PhotoCraft issue tracker — the ONLY safe way to touch
issues/issues.db.

Append-only by construction: no remove/delete commands exist, and UPDATEs are
whitelisted to the mutable status columns. Every operation is logged to the
append-only `events` table. The database is the cross-project per-issue
record; per-call machine records stay in each project's mcp-calls/ corpus.

Data lives in the machine-local home `~/.photocraft-automation/` (override
with $PHOTOCRAFT_AUTOMATION_HOME) so every install of the skill — any
checkout, any working directory — shares one tracker.

Schema is created automatically inside connect() (idempotent). All writes
use WAL + busy_timeout so parallel sessions can record concurrently.

Exit codes: 0 ok; 1 usage/validation error; 2 dedup-confirmation (still a
successful recording: the issue already existed and was confirmed).
"""
import argparse
import datetime
import json
import os
import pathlib
import re
import sqlite3
import sys

# Machine-local data home, shared by every install of the skill.
HOME_DIR = pathlib.Path(
    os.environ.get("PHOTOCRAFT_AUTOMATION_HOME", "~/.photocraft-automation")
).expanduser()
ISSUES_DIR = HOME_DIR / "issues"
DB_PATH = ISSUES_DIR / "issues.db"

TYPES = ("bug", "issue", "feature-request")
COMPONENTS = ("app", "control-protocol", "serve", "mcp-layer", "cli", "engine", "other")
STATUSES = ("open", "solved", "wontfix", "upstream-filed")

SCHEMA = """
CREATE TABLE IF NOT EXISTS issues (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_utc TEXT NOT NULL,
  updated_utc TEXT NOT NULL,
  name TEXT NOT NULL UNIQUE,
  slug TEXT NOT NULL UNIQUE,
  type TEXT NOT NULL CHECK(type IN ('bug','issue','feature-request')),
  component TEXT NOT NULL CHECK(component IN ('app','control-protocol','serve','mcp-layer','cli','engine','other')),
  description TEXT NOT NULL,
  file_path TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open','solved','wontfix','upstream-filed')),
  github_url TEXT,
  first_seen_project TEXT NOT NULL,
  first_seen_date TEXT NOT NULL,
  occurrence_count INTEGER NOT NULL DEFAULT 1,
  evidence TEXT
);
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts_utc TEXT NOT NULL,
  issue_id INTEGER NOT NULL,
  event TEXT NOT NULL,
  detail TEXT
);
"""

MD_TEMPLATE = """---
name: {name}
type: {type}
component: {component}
status: {status}
github_url: {github_url}
first_seen_project: {first_seen_project}
first_seen_date: {date}
---

# {name}

## What happened

{description}

## Diagnosis

{diagnosis}

## {fix_heading}

{fix_body}

## Evidence

{evidence_lines}

## Occurrences

- {date} — first seen in {first_seen_project}

## Status history

- {date} — recorded as {status}
"""


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def today():
    return datetime.date.today().isoformat()


def connect():
    ISSUES_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=10000")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def slugify(text):
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return s[:80].strip("-")


def norm_name(name):
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def log_event(conn, issue_id, event, detail=""):
    conn.execute("INSERT INTO events (ts_utc, issue_id, event, detail) VALUES (?,?,?,?)",
                 (now(), issue_id, event, detail))


def find_existing(conn, slug, name):
    row = conn.execute("SELECT * FROM issues WHERE slug=?", (slug,)).fetchone()
    if row:
        return row
    rows = conn.execute("SELECT * FROM issues", ()).fetchall()
    target = norm_name(name)
    for r in rows:
        if norm_name(r["name"]) == target:
            return r
    return None


def append_confirms(file_path, project, date, note):
    p = HOME_DIR / file_path
    with p.open("a", encoding="utf-8") as f:
        f.write(f"- {date} — confirmed again in {project}"
                + (f" ({note})" if note else "") + "\n")


def evidence_list(raw):
    if not raw:
        return []
    return [p.strip() for p in raw.split(",") if p.strip()]


def emit(args, data):
    if getattr(args, "json", False):
        print(json.dumps(data, indent=1, default=str))
    else:
        for k, v in data.items():
            print(f"{k}: {v}")


def cmd_init(args):
    conn = connect()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    print(f"ok: tracker ready at {DB_PATH}")


def cmd_add(args):
    if args.type not in TYPES:
        sys.exit(f"error: --type must be one of {TYPES}")
    if args.component not in COMPONENTS:
        sys.exit(f"error: --component must be one of {COMPONENTS}")
    slug = args.slug or slugify(args.name)
    if not slug:
        sys.exit("error: could not derive a slug; pass --slug")
    date = today()
    ev = evidence_list(args.evidence)
    conn = connect()
    try:
        conn.executescript(SCHEMA)  # idempotent even if init was skipped
        existing = find_existing(conn, slug, args.name)
        if existing:
            count = existing["occurrence_count"] + 1
            conn.execute("UPDATE issues SET occurrence_count=?, updated_utc=? WHERE id=?",
                         (count, now(), existing["id"]))
            log_event(conn, existing["id"], "confirmed",
                      f"project={args.project} occurrence={count}")
            conn.commit()
            try:
                append_confirms(existing["file_path"], args.project, date, args.note)
            except OSError:
                pass
            print(f"confirmed: id={existing['id']} slug={existing['slug']} "
                  f"occurrence_count={count} (no new row)")
            sys.exit(2)
        fname = f"{date}-{args.type}-{slug}.md"
        rel = f"issues/{fname}"
        fpath = HOME_DIR / rel
        if fpath.exists():
            sys.exit(f"error: issue file {rel} already exists but no db row — "
                     f"pass a different --slug")
        status = "open"
        github_url = ""
        ev_lines = "\n".join(f"- {p}" for p in ev) or "- (none recorded)"
        diagnosis = args.diagnosis or "(to be filled by the recording lane)"
        if args.type == "feature-request":
            fix_heading, fix_body = "Feature ask", args.workaround or "(see description)"
        else:
            fix_heading, fix_body = "Workaround / fix", args.workaround or "(none found yet)"
        fpath.write_text(MD_TEMPLATE.format(
            name=args.name, type=args.type, component=args.component, status=status,
            github_url=github_url or "none", first_seen_project=args.project, date=date,
            description=args.description, diagnosis=diagnosis,
            fix_heading=fix_heading, fix_body=fix_body,
            evidence_lines=ev_lines), encoding="utf-8")
        cur = conn.execute(
            "INSERT INTO issues (created_utc, updated_utc, name, slug, type, component,"
            " description, file_path, status, github_url, first_seen_project,"
            " first_seen_date, occurrence_count, evidence)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (now(), now(), args.name, slug, args.type, args.component,
             args.description, rel, status, None, args.project, date, 1,
             json.dumps(ev)))
        iid = cur.lastrowid
        log_event(conn, iid, "created", f"project={args.project}")
        conn.commit()
        print(f"recorded: id={iid} slug={slug} file={rel}")
    finally:
        conn.close()


def resolve(conn, key):
    if key.isdigit():
        row = conn.execute("SELECT * FROM issues WHERE id=?", (int(key),)).fetchone()
        if row:
            return row
    return conn.execute("SELECT * FROM issues WHERE slug=?", (key,)).fetchone()


def guard_status(conn, row, to_status):
    if row["status"] == to_status:
        print(f"no-op: id={row['id']} already {to_status}")
        return None
    return to_status


def cmd_set_solved(args):
    conn = connect()
    try:
        row = resolve(conn, args.issue)
        if not row:
            sys.exit(f"error: no issue '{args.issue}'")
        new = guard_status(conn, row, "solved")
        if new is None:
            return
        conn.execute("UPDATE issues SET status=?, updated_utc=? WHERE id=?",
                     (new, now(), row["id"]))
        log_event(conn, row["id"], "solved", args.note or "")
        conn.commit()
        print(f"ok: id={row['id']} '{row['name']}' -> solved")
    finally:
        conn.close()


def cmd_reopen(args):
    conn = connect()
    try:
        row = resolve(conn, args.issue)
        if not row:
            sys.exit(f"error: no issue '{args.issue}'")
        if row["status"] == "open":
            print(f"no-op: id={row['id']} already open")
            return
        conn.execute("UPDATE issues SET status='open', updated_utc=? WHERE id=?",
                     (now(), row["id"]))
        log_event(conn, row["id"], "reopened", args.note or "")
        conn.commit()
        print(f"ok: id={row['id']} '{row['name']}' -> open")
    finally:
        conn.close()


def cmd_set_github(args):
    if not re.match(r"^https://", args.url):
        sys.exit("error: --url must be an https URL")
    conn = connect()
    try:
        row = resolve(conn, args.issue)
        if not row:
            sys.exit(f"error: no issue '{args.issue}'")
        if row["github_url"] == args.url:
            print(f"no-op: id={row['id']} github_url already set")
            return
        new_status = "upstream-filed" if row["status"] == "open" else row["status"]
        conn.execute("UPDATE issues SET github_url=?, status=?, updated_utc=? WHERE id=?",
                     (args.url, new_status, now(), row["id"]))
        log_event(conn, row["id"], "github-filed", args.url)
        conn.commit()
        print(f"ok: id={row['id']} '{row['name']}' github={args.url} status={new_status}")
    finally:
        conn.close()


def cmd_append_evidence(args):
    new = evidence_list(args.evidence)
    if not new:
        sys.exit("error: --evidence lists no paths")
    conn = connect()
    try:
        row = resolve(conn, args.issue)
        if not row:
            sys.exit(f"error: no issue '{args.issue}'")
        old = json.loads(row["evidence"] or "[]")
        merged = old + [p for p in new if p not in old]
        conn.execute("UPDATE issues SET evidence=?, updated_utc=? WHERE id=?",
                     (json.dumps(merged), now(), row["id"]))
        log_event(conn, row["id"], "evidence-added", "; ".join(new))
        conn.commit()
        p = HOME_DIR / row["file_path"]
        with p.open("a", encoding="utf-8") as f:
            f.write("\n## Evidence (post-added)\n\n" + "\n".join(f"- {x}" for x in new) + "\n")
        print(f"ok: id={row['id']} evidence now {len(merged)} path(s)")
    finally:
        conn.close()


def cmd_list(args):
    conn = connect()
    try:
        q = "SELECT * FROM issues WHERE 1=1"
        params = []
        if args.type:
            q += " AND type=?"; params.append(args.type)
        if args.status:
            q += " AND status=?"; params.append(args.status)
        if args.component:
            q += " AND component=?"; params.append(args.component)
        if args.unfiled:
            q += " AND github_url IS NULL"
        q += " ORDER BY id"
        rows = conn.execute(q, params).fetchall()
        if getattr(args, "json", False):
            print(json.dumps([dict(r) for r in rows], indent=1, default=str))
            return
        if not rows:
            print("no issues match")
            return
        for r in rows:
            gh = r["github_url"] or "-"
            print(f"[{r['id']:>3}] {r['type']:<15} {r['component']:<17} "
                  f"{r['status']:<15} occ={r['occurrence_count']:<3} gh={gh:<4} "
                  f"{r['name']}  ({r['slug']})")
        print(f"— {len(rows)} issue(s)")
    finally:
        conn.close()


def cmd_show(args):
    conn = connect()
    try:
        row = resolve(conn, args.issue)
        if not row:
            sys.exit(f"error: no issue '{args.issue}'")
        if getattr(args, "json", False):
            print(json.dumps(dict(row), indent=1, default=str))
            return
        for k in row.keys():
            print(f"{k}: {row[k]}")
        print("md file: " + str(HOME_DIR / row["file_path"]))
        evs = conn.execute("SELECT ts_utc, event, detail FROM events WHERE issue_id=?"
                           " ORDER BY id", (row["id"],)).fetchall()
        print("history:")
        for e in evs:
            print(f"  {e['ts_utc']}  {e['event']}  {e['detail']}")
    finally:
        conn.close()


def cmd_search(args):
    conn = connect()
    try:
        like = f"%{args.text}%"
        rows = conn.execute(
            "SELECT * FROM issues WHERE name LIKE ? OR description LIKE ? OR slug LIKE ?"
            " ORDER BY id", (like, like, like)).fetchall()
        for r in rows:
            print(f"[{r['id']:>3}] {r['type']:<15} {r['status']:<15} {r['name']}  ({r['slug']})")
        print(f"— {len(rows)} match(es)")
    finally:
        conn.close()


def cmd_stats(args):
    conn = connect()
    try:
        out = {"total": conn.execute("SELECT COUNT(*) FROM issues").fetchone()[0]}
        for col in ("type", "status", "component"):
            rows = conn.execute(f"SELECT {col}, COUNT(*) FROM issues GROUP BY {col}"
                                " ORDER BY 2 DESC").fetchall()
            out[col] = {r[0]: r[1] for r in rows}
        unfiled = conn.execute("SELECT COUNT(*) FROM issues WHERE github_url IS NULL"
                               " AND type != 'feature-request'").fetchone()[0]
        out["bugs_issues_unfiled"] = unfiled
        multi = conn.execute("SELECT COUNT(*) FROM issues WHERE occurrence_count > 1"
                             ).fetchone()[0]
        out["multi_session_issues"] = multi
        emit(args, out)
    finally:
        conn.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="create db + schema (idempotent)")

    p = sub.add_parser("add", help="record an issue (dedups automatically)")
    p.add_argument("--name", required=True, help="short human title (unique)")
    p.add_argument("--type", required=True, choices=TYPES)
    p.add_argument("--component", required=True, choices=COMPONENTS)
    p.add_argument("--description", required=True, help="1-3 line summary")
    p.add_argument("--project", required=True, help="project/session name for first-seen")
    p.add_argument("--evidence", default="", help="comma-separated evidence paths")
    p.add_argument("--diagnosis", default="", help="what the recording lane diagnosed")
    p.add_argument("--workaround", default="", help="workaround/fix found, or the feature ask")
    p.add_argument("--note", default="", help="extra note for confirms entries")
    p.add_argument("--slug", default=None, help="override slug (else derived from name)")

    p = sub.add_parser("list", help="list issues (filters)")
    p.add_argument("--type", choices=TYPES)
    p.add_argument("--status", choices=STATUSES)
    p.add_argument("--component", choices=COMPONENTS)
    p.add_argument("--unfiled", action="store_true", help="no github_url yet")

    p = sub.add_parser("show", help="full issue + event history")
    p.add_argument("issue", help="id or slug")

    p = sub.add_parser("search", help="substring search over name/description/slug")
    p.add_argument("text")

    p = sub.add_parser("set-solved", help="mark solved (no delete exists)")
    p.add_argument("issue")
    p.add_argument("--note", default="")

    p = sub.add_parser("reopen", help="set status back to open")
    p.add_argument("issue")
    p.add_argument("--note", default="")

    p = sub.add_parser("set-github", help="record the upstream GitHub issue URL")
    p.add_argument("issue")
    p.add_argument("--url", required=True)

    p = sub.add_parser("append-evidence", help="add evidence paths to an issue (append-only)")
    p.add_argument("issue")
    p.add_argument("--evidence", required=True, help="comma-separated paths to add")

    sub.add_parser("stats", help="counts by type/status/component")

    args = ap.parse_args()
    {"init": cmd_init, "add": cmd_add, "list": cmd_list, "show": cmd_show,
     "search": cmd_search, "set-solved": cmd_set_solved, "reopen": cmd_reopen,
     "set-github": cmd_set_github, "append-evidence": cmd_append_evidence,
     "stats": cmd_stats}[args.cmd](args)


if __name__ == "__main__":
    main()
