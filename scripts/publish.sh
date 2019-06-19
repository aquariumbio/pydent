#!/usr/bin/env bash
poetry run upver
poetry run verify
pip install twine -U
twine upload -r pypi dist/*
