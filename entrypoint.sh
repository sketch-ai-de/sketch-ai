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

if [[ "$script" == "chat_with_data.py" || "$script" == "load_data.py" ]]; then
    echo "Configure postgresql"
    # Required by postgresql
    chown -R postgres:postgres /var/lib/postgresql/16/main

    # Ensures that the owner of this folder is not weird after the docker container finishes
    cleanup() {
        chown -R 1000:1000 /var/lib/postgresql/16/main
    }
    trap cleanup EXIT INT TERM

    # Starts the postgresql service
    service postgresql start

    echo "Drop postgres database"
    su postgres -c "psql -U postgres -c \"DROP SCHEMA public CASCADE;\"" > /dev/null
    su postgres -c "psql -U postgres -c \"CREATE SCHEMA public;\"" > /dev/null
    su postgres -c "psql -U postgres -c \"GRANT ALL ON SCHEMA public TO postgres;\"" > /dev/null
    su postgres -c "psql -U postgres -c \"GRANT ALL ON SCHEMA public TO public;\"" > /dev/null

    su postgres -c "psql --command \"ALTER USER postgres with encrypted password 'postgres';\"" > /dev/null
    #su postgres -c "psql --command \"CREATE DATABASE postgres;\""
    echo "Create database and tables"
    su postgres -c "psql postgresql://postgres:postgres@127.0.0.1/postgres < db/postgresql_backup.sql" > /dev/null

fi

python3 "$script" "${@:2}"
exit 0
