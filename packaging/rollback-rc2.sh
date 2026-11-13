#!/bin/sh
set -eu
ROOT=${1:-/opt/hashburst}
STATE=${HB_NODE_STATE:-/var/lib/hashburst/node}
test "$(id -u)" -eq 0 || { echo "root required" >&2; exit 2; }
test -f "$ROOT/previous-release" || { echo "no previous release recorded" >&2; exit 3; }
PREV=$(cat "$ROOT/previous-release")
test -d "$PREV" || { echo "previous release missing: $PREV" >&2; exit 4; }
# Fail closed if an exploration has evidence of mutation without a terminal receipt.
# Do not delete or rewrite it: preserve the evidence for recovery/diagnosis.
for d in "$STATE"/exploration/explore-*; do
 [ -d "$d" ] || continue
 if [ -f "$d/pre-state.json" ] && [ ! -f "$d/receipt.signed.json" ]; then
  echo "BLOCKING: interrupted exploration requires recovery before executable rollback: $d" >&2
  exit 5
 fi
done
ln -sfn "$PREV" "$ROOT/current.next"
mv -Tf "$ROOT/current.next" "$ROOT/current"
echo "Rolled back executable release only; persistent identity, anti-replay and exploration evidence untouched at $STATE"
