#!/bin/bash

docker pull arizephoenix/phoenix
docker run -p 6006:6006 -p 4317:4317 -i -t arizephoenix/phoenix:latest