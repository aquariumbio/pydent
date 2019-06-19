#!/usr/bin/env bash
poetry run upver
poetry run verify
poetry publish -r testpypi --build
