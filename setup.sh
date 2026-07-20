#!/bin/bash

# Build the docker image
docker build -t attack-smt .

# Run the docker image
docker run --rm -it attack-smt