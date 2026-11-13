#!/bin/sh
set -eu
ROOT=${1:-/opt/hashburst}
STATE=${HB_NODE_STATE:-/var/lib/hashburst/node}
REL="$ROOT/releases/v0.1.0-rc1"
test "$(id -u)" -eq 0 || { echo "root required" >&2; exit 2; }
test -f release/manifest-v0.1.0-rc1.json
python3 tools/rc1_gate.py
mkdir -p "$ROOT/releases" "$STATE"
test ! -e "$REL" || { echo "release already installed" >&2; exit 3; }
mkdir "$REL"
cp -a hb_node.py src config schemas release "$REL/"
ln -sfn "$REL" "$ROOT/current.next"
if [ -L "$ROOT/current" ]; then readlink "$ROOT/current" > "$ROOT/previous-release"; fi
mv -Tf "$ROOT/current.next" "$ROOT/current"
echo "Installed v0.1.0-rc1; identity/anti-replay state untouched at $STATE"
