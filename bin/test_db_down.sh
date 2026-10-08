#!/bin/bash
# Run the tests with the real data.db_connect.is_db_up forced to return
# False, to prove no test depends on the real DB check. Restores
# data/db_connect.py afterwards, even on failure or Ctrl-C.
#
# Usage: bin/test_db_down.sh [PATH...]     (default: states counties server)
set -euo pipefail

cd "$(dirname "$0")/.."
DB_FILE=data/db_connect.py

if ! git diff --quiet -- "$DB_FILE"; then
    echo "$DB_FILE has uncommitted changes; refusing to modify it." >&2
    exit 1
fi
trap 'git checkout -q -- "$DB_FILE"' EXIT

sed -i '' '/^def is_db_up/,/return True/s/return True/return False/' "$DB_FILE"
if git diff --quiet -- "$DB_FILE"; then
    echo "Could not force is_db_up to False in $DB_FILE." >&2
    exit 1
fi

[ $# -eq 0 ] && set -- states counties server
echo "=== is_db_up forced to return False ==="
bin/test.sh "$@"
