PIP=pip3

.PHONY: docs  # necessary so it doesn't look for 'docs/makefile html'

init:
	$(PIP) install pipenv --upgrade
	pipenv install --dev --skip-lock


test:
	pipenv run tox


pylint:
	pipenv run pylint pydent


coverage:
	@echo "Coverage"
	pipenv run py.test --cov-config .coveragerc --verbose --cov-report term --cov-report xml --cov=pydent tests


docs:
	@echo "Updating docs"

	# copy README.md to README.rst format for Sphinx documentation
	# we can comment this out if we do not want to include the README.md in the sphinx documentation
	#pipenv run pandoc --from=markdown --to=rst --output=docsrc/README.rst README.md

	cd docsrc && pipenv run make html
	@echo "\033[95m\n\nBuild successful! View the docs homepage at docs/html/index.html.\n\033[0m"