#!/usr/bin/env bash

ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
EXEC_PATH=$PWD

cd $ROOT_DIR

docker compose  -f $ROOT_DIR/docker/docker-compose.yml down
docker compose  -f $ROOT_DIR/docker/docker-compose.yml up -d
                                
cd $EXEC_PATH
