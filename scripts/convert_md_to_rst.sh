#!/usr/bin/env bash

# the following converts markdown to rst format for sphinx documentation
pandoc --from=markdown --to=rst --output=../docs/README.rst ../Usage.md
pandoc --from=markdown --to=rst --output=../docs/DeveloperNotes.rst ../DeveloperNotes.md
pandoc --from=markdown --to=rst --output=../docs/Examples.rst ../Examples.md
pandoc --from=markdown --to=rst --output=../docs/Tests.rst ../Tests.md