#!/usr/bin/env bash

# entrypoint.sh currently only starts the web-based chat interface and is not
# used to add new data into the database.

set -e

# Check if the first argument has an extension of .py
# If not, default the first argument to be chat_with_data.py
script=${1:-chat_with_data.py}
if [[ ! "$script" =~ \.py$ ]]; then
    echo "Usage: ./entrypoint.sh <python_script.py> [args...]"
    exit 1
fi

python3 "$script" "${@:2}"
exit 0
