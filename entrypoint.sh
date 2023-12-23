#!/usr/bin/env bash

# entrypoint.sh currently only starts the web-based chat interface and is not
# used to add new data into the database.

set -e

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
su postgres -c "psql -U postgres -c \"DROP SCHEMA public CASCADE;\""
su postgres -c "psql -U postgres -c \"CREATE SCHEMA public;\""
su postgres -c "psql -U postgres -c \"GRANT ALL ON SCHEMA public TO postgres;\""
su postgres -c "psql -U postgres -c \"GRANT ALL ON SCHEMA public TO public;\""

su postgres -c "psql --command \"ALTER USER postgres with encrypted password 'postgres';\""
#su postgres -c "psql --command \"CREATE DATABASE postgres;\""
echo "Create database and tables"
su postgres -c "psql postgresql://postgres:postgres@127.0.0.1/postgres < postgresql_backup.sql"

# Calls the main script to chat with data
echo "Starting chat with data"
python3 chat_with_data.py