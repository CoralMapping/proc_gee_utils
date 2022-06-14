# Copyright Arizona State University 2021-2022
#
# Licensed under the Apache License, Version 2.0 (the "License").
# You may not use this file except in compliance with the License.
# A copy of the License is located at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# or in the "license" file accompanying this file. This file is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language governing
# permissions and limitations under the License.

MAKEFLAGS += --warn-undefined-variables

.POSIX:
SHELL := /bin/sh

.DEFAULT_GOAL := menu

archive := $(CURDIR)/dist/geeutils-*
pypi_repository := testpypi
pypi_repository_username := $(PYPI_REPOSITORY_USERNAME)
pypi_repository_password ?= $(PYPI_REPOSITORY_PASSWORD)
prerelease ?= b$(shell git rev-list --count HEAD ^develop)
python_quality_tools_image := gcr.io/coral-atlas/baseimages/python-quality-tools:latest

%:
	@:

.PHONY: menu
menu:
	@ grep -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-35s\033[0m %s\n", $$1, $$2}'

.PHONY: check
check:  ## Run Python quality tools
	# See https://circleci.com/docs/2.0/building-docker-images/#mounting-folders
	@- docker create -v /app --name app_files alpine:3.4 /bin/true && \
		docker cp . app_files:/app && \
		docker run --rm --volumes-from app_files $(python_quality_tools_image)
	@ docker rm app_files &>/dev/null

.PHONY: test
test:  $(shell find $(CURDIR)/geeutils -type f) ## Run the unit tests
	@ . tests/env.sh && pipenv run pytest

.PHONY: build
build:  $(archive) ## Build the Python archive
	@ :

$(archive): setup.py $(shell find $(CURDIR)/geeutils -type f)
	@ pipenv run python setup.py egg_info --tag-build=$(prerelease) sdist bdist_wheel

.PHONY: publish
publish:  $(archive) ## Publish the Python archive to the PyPi repository
	@ pipenv run python -m twine upload \
		--repository $(pypi_repository) \
		--username $(pypi_repository_username) \
		--password $(pypi_repository_password) \
		--disable-progress-bar \
		$(archive)
