#!/usr/bin/env bash
poetry run upver
poetry run verify
VER=$(poetry run version)
echo $VER