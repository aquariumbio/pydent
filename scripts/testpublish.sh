#!/usr/bin/env bash
poetry run upver
poetry run verify $1
make docs
poetry publish -r testpypi --build -n
