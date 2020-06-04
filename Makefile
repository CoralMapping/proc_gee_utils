MAKEFLAGS += --warn-undefined-variables

.POSIX:
SHELL := /bin/sh

.DEFAULT_GOAL := menu

archive := $(CURDIR)/dist/geeutils-*.tar.gz
pypi_repository_url := https://vulcin.jfrog.io/artifactory/api/pypi/pypi-coral-atlas
pypi_repository_username := coral-atlas-pip-write
pypi_repository_password ?= $(PYPI_REPOSITORY_PASSWORD)
beta_tag_suffix ?= -$(shell git symbolic-ref --short HEAD)

%:
	@:

.PHONY: menu
menu:
	@ grep -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-35s\033[0m %s\n", $$1, $$2}'

.PHONY: test
test:  $(shell find $(CURDIR)/geeutils -type f) ## Run the unit and integration tests
	@ . tests/env.sh && pipenv run pytest

.PHONY: build
build:  $(archive) ## Build the Python archive
	@ :

$(archive): setup.py $(shell find $(CURDIR)/geeutils -type f)
	@ pipenv run python setup.py egg_info --tag-build=$(beta_tag_suffix) sdist

.PHONY: publish
publish:  $(archive) ## Publish the Python archive to the PyPi repository
	@ pipenv run python -m twine upload \
		--repository-url $(pypi_repository_url) \
		--username $(pypi_repository_username) \
		--password $(pypi_repository_password) \
		--disable-progress-bar \
		$(archive)
