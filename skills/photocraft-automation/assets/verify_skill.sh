#!/usr/bin/env bash
# Deterministic half of the skill-creator verification checklist for this skill.
set -u
DIR="$(cd "$(dirname "$0")/.." && pwd)"
SKILL="$DIR/SKILL.md"
MEM="${PHOTOCRAFT_AUTOMATION_HOME:-$HOME/.photocraft-automation}/memory"
fail=0
ck() { if [ "$1" = 0 ]; then echo "PASS: $2"; else echo "FAIL: $2"; fail=1; fi }

python3 - "$SKILL" << 'PY'
import sys
d = {}
try:
    import yaml
    d = yaml.safe_load(open(sys.argv[1]).read().split('---')[1])
except Exception as e:
    print(f"FAIL: frontmatter YAML parse: {e}"); sys.exit(1)
import os
name = os.path.basename(os.path.dirname(os.path.abspath(sys.argv[1])))
print("PASS: frontmatter YAML parses" if d.get('name') == name else f"FAIL: name {d.get('name')} != dir {name}")
sys.exit(0 if d.get('name') == name else 1)
PY
[ $? -ne 0 ] && fail=1

grep -qE 'finish.current|slightly negative|past_due_grace|B1–B14' "$SKILL" \
  && { echo "FAIL: stale-law marker present"; fail=1; } || echo "PASS: no stale-law markers"

grep -qiE 'har[h]+aial' "$SKILL" "$MEM"/*.md 2>/dev/null \
  && { echo "FAIL: forbidden name token present (user law)"; fail=1; } || echo "PASS: no forbidden name token anywhere"

n_amd=$(grep -c '^## Amendment' "$SKILL")
[ "$n_amd" -eq 0 ] && echo "PASS: no amendment blocks (current-state law only)" \
  || { echo "FAIL: $n_amd amendment block(s) present — refactor into current-state law"; fail=1; }

# No calendar dates in committed skill files; the runtime memory store
# keeps its own chronology outside the repo.
date_leaks=$(grep -rInE '\b20[0-9]{2}-[01][0-9]-[0-3][0-9]\b' "$DIR" \
  | grep -v 'verify_skill.sh')
if [ -n "$date_leaks" ]; then echo "FAIL: date literal in committed file:"; echo "$date_leaks"; fail=1; else echo "PASS: no calendar dates"; fi

# Committed files reference the memory store as a whole only; a memory/
# path naming an individual entry is a personal-data citation.
mem_cites=$(grep -rInE 'memory/[A-Za-z0-9]' "$DIR" \
  --include='*.md' --include='*.py' --include='*.sh' \
  --include='*.yaml' --include='*.json' 2>/dev/null \
  | grep -v 'verify_skill.sh')
if [ -n "$mem_cites" ]; then echo "FAIL: memory-entry citation in committed file:"; echo "$mem_cites"; fail=1; else echo "PASS: no memory-entry citations (store referenced as a whole only)"; fi

if ls "$MEM"/*.md >/dev/null 2>&1; then
  bad_mem=$(grep -L '^date:' "$MEM"/*.md 2>/dev/null)
  [ -z "$bad_mem" ] && echo "PASS: memory entries carry frontmatter" || { echo "FAIL: memory entry missing date: $bad_mem"; fail=1; }
else
  echo "PASS: no memory store yet (fresh home) — frontmatter check skipped"
fi

# Privacy gate: no absolute local home paths in committed skill files.
# (/home/<user> placeholders are the sanctioned form; the literal class
# here breaks the regex, so this script does not match itself.)
leaks=$(grep -rInE '/home/[A-Za-z0-9_.-]+/' "$DIR" \
  --include='*.md' --include='*.py' --include='*.sh' \
  --include='*.yaml' --include='*.json' 2>/dev/null \
  | grep -vF '/home/<user>' | grep -v 'verify_skill.sh')
[ -z "$leaks" ] && echo "PASS: no absolute local home paths" \
  || { echo "FAIL: local user path leak:"; echo "$leaks"; fail=1; }

# No personal home-layout paths either: ~/<dir> (non-dot) names a user's
# own tree; ~/.<dir> standard locations are sanctioned. config.example.json
# carries the fill-in placeholder schema, so its example values are exempt.
tilde_leaks=$(grep -rInE '~/[A-Za-z0-9]' "$DIR" \
  --include='*.md' --include='*.py' --include='*.sh' \
  --include='*.yaml' --include='*.json' 2>/dev/null \
  | grep -v 'verify_skill.sh' | grep -v 'config.example.json')
[ -z "$tilde_leaks" ] && echo "PASS: no personal home-layout paths" \
  || { echo "FAIL: personal home-layout path leak:"; echo "$tilde_leaks"; fail=1; }

exit $fail
