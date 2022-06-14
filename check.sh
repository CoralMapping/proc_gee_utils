#! /bin/sh

set -e

echo 'Running Black'
black --check .
echo

echo 'Running Flake8'
flake8 .
echo

echo 'Running mypy'
mypy --install-types --non-interactive --namespace-packages --explicit-package-bases --ignore-missing-imports .
echo

echo 'Running usort'
usort check .
echo

echo 'Done'
