#!/bin/bash
# Usage: recheck.sh <work dir> <config dir>
# Runs each saved query again and compares the row count with its extract (same base name, .tsv).
# Line 1 of a .sql file names its source script: "-- source: <name>" runs <config dir>/sources/<name>.sh.
# Prints one line per query: MATCH, MISMATCH or NO-SOURCE. Exit 0 = all MATCH.
set -u
sources="$(cd "$2" && pwd)/sources"
cd "$1" || exit 2

status=0
while IFS= read -r sql; do
    tsv="${sql%.sql}.tsv"
    script="$sources/$(sed -n '1s/^-- source: //p' "$sql").sh"
    if [ ! -x "$script" ]; then
        printf 'NO-SOURCE\t%s\n' "$sql"
        status=1
        continue
    fi
    saved=$(($(wc -l <"$tsv")))
    fresh=$(($("$script" "$(cat "$sql")" </dev/null | wc -l)))
    if [ "$saved" -eq "$fresh" ]; then
        printf 'MATCH\t%s\t%s\n' "$sql" "$saved"
    else
        printf 'MISMATCH\t%s\tsaved=%s\tfresh=%s\n' "$sql" "$saved" "$fresh"
        status=1
    fi
done < <(grep -rl --include='*.sql' '^-- source: ' . | sort)
exit $status
