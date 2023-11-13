#!/usr/bin/env bash
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
su postgres -c "psql --command \"ALTER USER postgres with encrypted password 'postgres';\""

# Calls the main script to chat with data
./chat_with_data.py "$@"
