#!/usr/bin/env bash
# Gate-2 renderer launcher for this skill. Prefers an mmdr already on
# PATH; otherwise fetches the matching upstream release asset into a
# per-user cache on first run and reuses it afterwards.
#
# Contract (sanctioned carve-out in the repo AGENTS.md): one specific
# upstream release asset, HTTPS only, confined to a per-user cache, no
# privilege escalation, no package managers. Failure to fetch is
# reported and exits nonzero — the render gate never silently passes.
set -euo pipefail

REPO="1jehuang/mermaid-rs-renderer"
API="https://api.github.com/repos/${REPO}/releases/latest"

die() {
  printf 'mmdr unavailable: %s\n' "$1" >&2
  exit 1
}

if command -v mmdr >/dev/null 2>&1; then
  exec mmdr "$@"
fi

for tool in curl tar; do
  command -v "$tool" >/dev/null 2>&1 ||
    die "missing host tool '${tool}'; install mmdr manually or use a documented fallback renderer"
done

case "$(uname -s)" in
  Linux) os="unknown-linux-gnu" ;;
  Darwin) os="apple-darwin" ;;
  MINGW* | MSYS* | CYGWIN*) os="pc-windows-msvc" ;;
  *) die "unsupported OS '$(uname -s)'" ;;
esac

case "$(uname -m)" in
  x86_64 | amd64) arch="x86_64" ;;
  arm64 | aarch64) arch="aarch64" ;;
  *) die "unsupported architecture '$(uname -m)'" ;;
esac

target="${arch}-${os}"

cache_home="${XDG_CACHE_HOME:-${HOME:-/}/.cache}/mermaid-diagrams"
mkdir -p "$cache_home" 2>/dev/null || die "cannot create the cache directory"

# Any previously cached binary for this target runs before any network
# call, so a transient API failure never defeats a warm cache.
for cached in "${cache_home}"/mmdr-"${target}"-v*; do
  [ -x "$cached" ] || continue
  if "$cached" --version >/dev/null 2>&1; then
    exec "$cached" "$@"
  fi
done

release_json="$(curl -fsSL --max-time 30 "$API" 2>/dev/null)" ||
  die "no runnable cached renderer, and could not read the latest release metadata from ${API}"

# The API answers with single-line JSON, so match the field itself rather
# than a line — a line match would mis-parse any earlier key.
version="$(printf '%s' "$release_json" |
  grep -oE '"tag_name"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 |
  sed -E 's/.*"([^"]*)"$/\1/' || true)"
[ -n "$version" ] || die "could not determine the latest release version (rate-limited API?)"
version="${version//[[:space:]]/}"
case "$version" in
  v[0-9]*) ;;
  *) die "unexpected release tag '${version}'" ;;
esac

if [ "$os" = "pc-windows-msvc" ]; then
  command -v unzip >/dev/null 2>&1 || die "missing host tool 'unzip'"
  url="https://github.com/${REPO}/releases/download/${version}/mmdr-${target}.zip"
  archive="${cache_home}/mmdr-${target}-${version}.zip"
  member="mmdr.exe"
else
  url="https://github.com/${REPO}/releases/download/${version}/mmdr-${target}.tar.gz"
  archive="${cache_home}/mmdr-${target}-${version}.tar.gz"
  member="mmdr"
fi

binary="${cache_home}/mmdr-${target}-${version}"

tmp="${archive}.partial"
curl -fsSL --max-time 300 "$url" -o "$tmp" ||
  {
    rm -f "$tmp"
    die "download failed: ${url}"
  }
mv -f "$tmp" "$archive"

if [ "$os" = "pc-windows-msvc" ]; then
  unzip -o -q "$archive" "$member" -d "$cache_home" || die "extraction failed: ${archive}"
else
  tar -xzf "$archive" -C "$cache_home" "./${member}" || die "extraction failed: ${archive}"
fi

[ -f "${cache_home}/${member}" ] || die "release asset did not contain '${member}'"
mv -f "${cache_home}/${member}" "$binary"
chmod +x "$binary"

exec "$binary" "$@"
