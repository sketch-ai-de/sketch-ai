#!/usr/bin/env bash
# A helper script to run the docker container
# Usage: ./run.sh <python-script.py> <args...>
# By default, the python script is set to chat_with_data.py
# For example:
#   To start the chat_with_data.py script: ./run.sh
#   To run an example script: ./run.sh examples/open_ai_like.py
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Build the docker image
docker build -t sketch-ai .

# Remove the docker container if it exists
docker rm -f sketch-ai-container || true

# Check if the db/chroma_db directory exists
if [ ! -d "${SCRIPT_DIR}/db/chroma_db" ]; then
    echo "WARNING:"
    echo "    db/chroma_db directory not found. Creating directory..."
    mkdir ${SCRIPT_DIR}/db/chroma_db
fi

# TODO(qu): Remove this after we set up the connection to the postgresql database on Azure
# Check if db/postgresql_backup.sql file exists
if [ ! -f "${SCRIPT_DIR}/db/postgresql_backup.sql" ]; then
    echo "Error:"
    echo "    db/postgresql_backup.sql file not found. Please place the file in the same directory as this script."
    exit 1
fi

# Run the docker container with all arguments
docker run -v ${SCRIPT_DIR}/db:/sketch-ai/db \
       -p 7860:7860 -p 8080:8080 --name sketch-ai-container -ti sketch-ai "$@"
