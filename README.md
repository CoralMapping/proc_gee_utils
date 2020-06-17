## Google Earth Engine (GEE) Utilities
This project provides a few simple utility functions for interacting with GEE.

### Installation
This package is hosted on a private Python Package Index (PyPi) repository. Before installing it, add this `source` to your Pipfile:

```
[[source]]
name = "pypi-coral-atlas"
url = "https://coral-atlas-pip-read:'${PYPI_REPOSITORY_PASSWORD}'@vulcin.jfrog.io/artifactory/api/pypi/pypi-coral-atlas/simple"
verify_ssl = true
```

As the source indicates, a password with read permissions on the PyPi repository is expected to be provided via the `PYPI_REPOSITORY_PASSWORD` environment variable.  This password is stored in Vault, so set the environment variable with this command:

```
$ export PYPI_REPOSITORY_PASSWORD="$(vault read --field=value coral-atlas/main/pypi-coral-atlas-read)"
```

Once the source has been added to your Pipfile, install the package like any other:

```
$ pipenv install proc_gee_utils = "==0.0.1"
```

### Authentication
To function properly, this code needs credentials that it can use to authenticate against the Google Cloud Storage API.  Credentials can be provided in one of three ways, and the code will look for them in this order:

1. Service Account Key.

Before running this code, create an environment variable named `SERVICE_ACCOUNT_KEY` containing the JSON key for a Google Cloud service account with the necessary permissions to perform the actions you're trying to perform in GEE.

2. Personal Credentials set in advance.

Before running this code, authenticate with the Google Earth Engine API using the `earthengine` command line tool:
```
$ earthengine authenticate
```

3. Personal Credentials provided on the fly.

If neither of the above credentials are available when the code runs, you will be prompted to authenticate.


### Continuous Integration

[CircleCI continuous integration](https://circleci.com) is configured to test this code, build a distributable package, and publish it to [a private Python Package Index (PyPi) repository](https://vulcin.jfrog.io/artifactory/pypi-coral-atlas/).

CI is configured in the `.circleci/` directory.

In order to publish the package, CircleCI needs a password with write permissions to the PyPi repository.  If it doesn't already exist, [create an environment variable](https://circleci.com/docs/2.0/env-vars/) in the CircleCI project named `PYPI_REPOSITORY_PASSWORD` and give it the password from Vault:

```
$ vault read --field=value coral-atlas/main/pypi-coral-atlas-write
```

CircleCI simply calls targets in the `Makefile`, but the image can also be built, tested, and pushed locally using the corresponding `make` targets:

```
$ make [test, build, publish]
```

NOTE: The `Makefile` requires the PyPi password in an environment variable as described above.
