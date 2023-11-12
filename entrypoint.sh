#!/usr/bin/env bash

service postgresql start
su postgres -c "psql --command \"ALTER USER postgres with encrypted password 'postgres';\""

exec ./chat_with_data.py "$@"
