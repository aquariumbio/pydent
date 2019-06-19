#!/usr/bin/env bash
poetry config repositories.pypi https://pypi.org/
poetry config http-basic.pypi $1 $2