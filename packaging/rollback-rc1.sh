#!/bin/sh
set -eu
ROOT=${1:-/opt/hashburst}
STATE=${HB_NODE_STATE:-/var/lib/hashburst/node}
test "$(id -u)" -eq 0 || { echo "root required" >&2; exit 2; }
test -f "$ROOT/previous-release" || { echo "no previous release recorded" >&2; exit 3; }
PREV=$(cat "$ROOT/previous-release")
test -d "$PREV" || { echo "previous release missing: $PREV" >&2; exit 4; }
ln -sfn "$PREV" "$ROOT/current.next"
mv -Tf "$ROOT/current.next" "$ROOT/current"
echo "Rolled back executable release only; identity/anti-replay state untouched at $STATE"
