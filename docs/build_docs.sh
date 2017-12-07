#!/usr/bin/env bash

rm -rf _autosummary

#pip install pandoc

# convert .md to .rst
pandoc --from=markdown --to=rst --output=README.rst ../Usage.md
pandoc --from=markdown --to=rst --output=DeveloperNotes.rst ../DeveloperNotes.md
pandoc --from=markdown --to=rst --output=Examples.rst ../Examples.md
pandoc --from=markdown --to=rst --output=Tests.rst ../Tests.md
pandoc --from=markdown --to=rst --output=CreatingDocs.rst ../CreatingDocs.md

make html