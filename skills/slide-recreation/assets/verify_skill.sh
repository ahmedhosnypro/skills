#!/usr/bin/env bash
# Deterministic authoring gate for slide-recreation. Run before every push.
# Bash + python3 + grep only.
set -u
DIR="$(cd "$(dirname "$0")/.." && pwd)"
SKILL="$DIR/SKILL.md"
fail=0
ck() { if [ "$1" = 0 ]; then echo "PASS: $2"; else echo "FAIL: $2"; fail=1; fi }

python3 - "$SKILL" << 'PY'
import os, re, sys
try:
    import yaml
except Exception as e:
    print(f"FAIL: pyyaml unavailable: {e}"); sys.exit(1)
try:
    d = yaml.safe_load(open(sys.argv[1]).read().split('---')[1])
except Exception as e:
    print(f"FAIL: frontmatter YAML parse: {e}"); sys.exit(1)
name = os.path.basename(os.path.dirname(os.path.abspath(sys.argv[1])))
ok = d.get('name') == name
print("PASS: frontmatter YAML parses" if ok else f"FAIL: name {d.get('name')} != dir {name}")
if not ok: sys.exit(1)
if not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', str(d.get('version', ''))):
    print(f"FAIL: version {d.get('version')!r} is not semver"); sys.exit(1)
desc = str(d.get('description', ''))
if 'Use whenever' not in desc or 'Do NOT use for' not in desc:
    print("FAIL: description must carry trigger conditions + negative scope"); sys.exit(1)
print(f"PASS: version {d['version']} + trigger-condition description with negative scope")
PY
[ $? -ne 0 ] && fail=1

# Prose with fenced code blocks stripped (their contents are data/demos).
prose="$(mktemp)"; trap 'rm -f "$prose"' EXIT
find "$DIR" -type f \( -name '*.md' -o -name '*.sh' -o -name '*.js' \
  -o -name '*.py' -o -name '*.json' -o -name '*.xml' \) ! -name 'verify_skill.sh' \
  -exec awk '/^```/ { fence = !fence; next } !fence { print FILENAME ":" FNR "\t" $0 }' {} + > "$prose"

n_amd=$(grep -c '^## Amendment' "$SKILL")
[ "$n_amd" -eq 0 ] && echo "PASS: no amendment blocks (current-state law only)" \
  || { echo "FAIL: $n_amd amendment block(s) present"; fail=1; }

n_sk=$(wc -l < "$SKILL")
[ "$n_sk" -lt 500 ] && echo "PASS: SKILL.md is $n_sk lines (< 500)" \
  || { echo "FAIL: SKILL.md is $n_sk lines (>= 500)"; fail=1; }

# Reference/notes files stay readable: each under 300 lines.
for rf in "$DIR"/references/*.md; do
  n=$(wc -l < "$rf")
  [ "$n" -lt 300 ] && echo "PASS: references/$(basename "$rf") is $n lines (< 300)" \
    || { echo "FAIL: references/$(basename "$rf") is $n lines (>= 300)"; fail=1; }
done

# No calendar dates anywhere in skill text.
! grep -E '\b20[0-9]{2}-[01][0-9]-[0-3][0-9]\b' "$prose" >/dev/null
ck $? "no calendar dates in text"

# No local user paths (sanctioned form is /home/<user> or ~).
leaks=$(grep -rInE '/home/[A-Za-z0-9_.-]+/' "$DIR" \
  --include='*.md' --include='*.sh' --include='*.js' --include='*.py' \
  --include='*.json' --include='*.xml' \
  | grep -vF '/home/<user>' | grep -v 'verify_skill.sh')
[ -z "$leaks" ] && echo "PASS: no personal user paths" \
  || { echo "FAIL: personal user path leak:"; echo "$leaks"; fail=1; }

# No privileged or system-mutating command text.
! grep -inE '(^|[^a-z])(sudo|killall|pkill)([^a-z]|$)' "$prose" >/dev/null
ck $? "no sudo/kill command text"
! grep -inE '\b(curl|wget|yt-dlp)[[:space:]]' "$prose" >/dev/null
ck $? "no download command text"
! grep -inE '[^a-z]kill[[:space:]]|-9[[:space:]]' "$prose" >/dev/null
ck $? "no process-kill recipes"

# Private-registry tokens: this skill was distilled from a private project;
# none of its identifiers may appear in the published form.
while IFS= read -r tok; do
  [ -z "$tok" ] && continue
  hits=$(grep -inF -- "$tok" "$prose" 2>/dev/null | head -3)
  if [ -n "$hits" ]; then
    echo "FAIL: private token '$tok' leaked:"; echo "$hits"; fail=1
  fi
done << 'TOKENS'
ai_llm_slides
ml-intro
IronRouter
glm-5.3
localhost:17844
analyze-image-key
DSAI 308
Zewail
novpn
15_progress
16_vision_gate
17_worker_instructions
18_omml_wrapper
/scripts/1[0-9]_
founder
TOKENS
[ "$fail" -eq 0 ] && echo "PASS: no private-project tokens" || true

# Every reference named in SKILL.md exists.
miss=0
for ref in $(grep -oE 'references/[A-Za-z0-9._-]+' "$SKILL" | sort -u); do
  if [ ! -e "$DIR/$ref" ] && [ ! -e "$DIR/references/${ref#references/}" ]; then
    case "$ref" in
      references/patterns/*) ;;  # library paths checked by index below
      *) echo "FAIL: SKILL.md references missing target: $ref"; miss=1 ;;
    esac
  fi
done
[ "$miss" -eq 0 ] && echo "PASS: every SKILL.md reference target exists"
[ "$miss" -ne 0 ] && fail=1

# Pattern index consistency: index entries <-> library dirs, entry files exist.
python3 - "$DIR/references/patterns/index.json" "$DIR/references/patterns" << 'PY'
import json, os, sys
idx_p, lib_p = sys.argv[1], sys.argv[2]
idx = json.load(open(idx_p))
names = [p["name"] for p in idx["patterns"]]
ok = True
for p in idx["patterns"]:
    f = os.path.join(lib_p, p["file"])
    if not os.path.isfile(f):
        print(f"FAIL: index entry {p['name']} -> missing file {p['file']}"); ok = False
dirs = sorted(d for d in os.listdir(lib_p) if os.path.isdir(os.path.join(lib_p, d)))
extra = [d for d in dirs if d not in names]
missing = [n for n in names if n not in dirs]
if extra:
    print(f"FAIL: pattern dirs missing from index: {extra}"); ok = False
if missing:
    print(f"FAIL: index names without a dir: {missing}"); ok = False
print(f"PASS: pattern index consistent ({len(names)} patterns)" if ok else "FAIL: pattern index inconsistent")
sys.exit(0 if ok else 1)
PY
[ $? -ne 0 ] && fail=1

# Helpers exist and parse (ast — no bytecode side effects).
for py in "$DIR"/scripts/*.py; do
  [ -e "$py" ] || continue
  if python3 -c "import ast,sys; ast.parse(open(sys.argv[1]).read())" "$py" 2>/dev/null; then
    echo "PASS: scripts/$(basename "$py") parses"
  else
    echo "FAIL: scripts/$(basename "$py") syntax error"; fail=1
  fi
done

exit $fail
