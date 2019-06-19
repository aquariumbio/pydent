#!/usr/bin/env bash
poetry config repositories.testpypi https://test.pypi.org/legacy/
poetry config http-basic.testpypi $1 $2