#!/bin/bash

docker-compose up -d
docker-compose exec nose nosetests --nocapture tests/
