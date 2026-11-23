#!/bin/bash
# Usage: watch.sh <config dir> <from> <to>
# Runs each query in <config dir>/watch/ for the window (UTC). A query holds __FROM__ and __TO__.
# Line 1 of a query names its source script: "-- source: <name>" runs <config dir>/sources/<name>.sh.
# Prints one line per query: HIT (rows found), QUIET or ERROR. Exit 0 = all QUIET.
set -u
shopt -s nullglob
config=$(cd "$1" && pwd)

status=0
for sql in "$config"/watch/*.sql; do
    script="$config/sources/$(sed -n '1s/^-- source: //p' "$sql").sh"
    query=$(sed -e "s|__FROM__|$2|g" -e "s|__TO__|$3|g" "$sql")
    rows=$(($("$script" "$query" </dev/null | wc -l) - 1))
    if [ "$rows" -lt 0 ]; then
        printf 'ERROR\t%s\n' "$sql"
        status=1
    elif [ "$rows" -gt 0 ]; then
        printf 'HIT\t%s\t%s\n' "$sql" "$rows"
        status=1
    else
        printf 'QUIET\t%s\n' "$sql"
    fi
done
exit $status
