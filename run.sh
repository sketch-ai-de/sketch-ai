#!/usr/bin/env bash
# A helper script to run the docker container
# Usage: ./run.sh <python-script.py> <args...>
# By default, the python script is set to chat_with_data.py
# For example:
#   To start the chat_with_data.py script: ./run.sh
#   To run an example script: ./run.sh examples/open_ai_like.py

# Build the docker image
docker build -t sketch-ai .

# Remove the docker container if it exists
docker rm -f sketch-ai-container || true

# Run the docker container with all arguments
docker run  -p 7860:7860 -p 8080:8080 --name sketch-ai-container -ti sketch-ai "$@"
