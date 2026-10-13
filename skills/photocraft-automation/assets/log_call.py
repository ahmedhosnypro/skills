#!/usr/bin/env python3
"""Log one PhotoCraft MCP/CLI/control call into the project corpus."""
import argparse
import datetime
import json
import pathlib
import re
import sys

HEX64 = re.compile(r"\b[0-9a-fA-F]{64}\b")


def redact(value):
    if isinstance(value, dict):
        return {k: "***" if "token" in k.lower() else redact(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    if isinstance(value, str):
        return HEX64.sub("***", value)
    return value


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir", help="per-document corpus dir, e.g. <artwork-root>/<slug>")
    ap.add_argument("--status", required=True, choices=["ok", "fail"])
    ap.add_argument("--tool", required=True, help="MCP tool, 'cli:<binary> <sub>' or 'tcp:<method>'")
    ap.add_argument("--params", help="call params as a JSON string")
    ap.add_argument("--cmd", help="exact CLI argv or TCP script text, when not an MCP tool call")
    ap.add_argument("--result", help="one-line outcome summary")
    ap.add_argument("--error", help="error text, failures only")
    ap.add_argument("--diagnosis", help="failure category, e.g. dpms-off, timeout-may-have-completed")
    ap.add_argument("--latency-ms", type=int)
    args = ap.parse_args()

    subdir = "succeeded" if args.status == "ok" else "failed"
    out = pathlib.Path(args.project_dir) / "mcp-calls" / subdir
    out.mkdir(parents=True, exist_ok=True)

    params = None
    if args.params:
        try:
            params = redact(json.loads(args.params))
        except json.JSONDecodeError:
            params = {"_raw": redact(args.params)}

    now = datetime.datetime.now(datetime.timezone.utc)
    entry = {
        "ts": now.isoformat(timespec="milliseconds"),
        "tool": args.tool,
        "params": params,
        "cmd": redact(args.cmd) if args.cmd else None,
        "result": args.result,
        "error": args.error,
        "diagnosis": args.diagnosis,
        "latency_ms": args.latency_ms,
    }
    slug = re.sub(r"[^a-zA-Z0-9_.-]+", "-", args.tool)[:60]
    path = out / f"{now.strftime('%Y%m%dT%H%M%S')}-{now.microsecond // 1000:03d}-{slug}.json"
    path.write_text(json.dumps(entry, indent=2) + "\n", encoding="utf-8")
    index_line = {"file": path.name}
    index_line.update({k: v for k, v in entry.items() if k != "params"})
    with (out / "index.jsonl").open("a", encoding="utf-8") as idx:
        idx.write(json.dumps(index_line) + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"log_call: {exc}", file=sys.stderr)
        sys.exit(1)
