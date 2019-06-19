#!/usr/bin/env bash
poetry version $1
poetry run upver
poetry run verify $1
make format
make docs
poetry publish -r testpypi --build -n
VER=$(poetry run version)
git add .
git commit -m "release $VER"
git tag $VER
git push
git push origin $VER