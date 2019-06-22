PIP=pip3

.PHONY: docs  # necessary so it doesn't look for 'docs/makefile html'


init:
	curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python
	poetry self:update
	poetry install
	poetry run pre-commit install

clean:
	rm -rf dist
	rm -rf pip-wheel-metadata
	rm -rf docs
	rm -rf .pytest_cache

test:
	poetry run python -m pytest


lint:
	poetry run pylint -E pydent


coverage:
	@echo "Coverage"
	poetry run py.test --cov-config .coveragerc --verbose --cov-report term --cov-report xml --cov=pydent tests


release:
	sh scripts/release.sh


pullversion:
	poetry run upver

docs: | pullversion
	@echo "Updating docs"

	# copy README.md to README.rst format for Sphinx documentation
	# we can comment this out if we do not want to include the README.md in the sphinx documentation

	rm -rf docs
	cd docsrc && poetry run make html
	find docs -type f -exec chmod 444 {} \;
	@echo "\033[95m\n\nBuild successful! View the docs homepage at docs/html/index.html.\n\033[0m"

	touch docs/.nojekyll
	open ./docs/index.html


doctest:
	rm -rf docs
	cd docsrc && poetry run make doctest


benchmark:
	rm -rf .benchmarks/images/*svg
	python -m pytest -m benchmark --benchmark-autosave --benchmark-max-time=0.1 --benchmark-group-by=func --benchmark-histogram=docsrc/_static/benchmark/histogram


format:
	poetry run black pydent
	poetry run black tests


testpublish:
	sh scripts/testpublish.sh


lock: | pullversion
	poetry update

build: | pullversion
	poetry build

tag: | pullversion
	sh scripts/tag.sh

hooks: .git/hooks
	cp scripts/* .git/hooks


klocs:
	find . -name '*.py' | xargs wc -l

tox:
	tox
