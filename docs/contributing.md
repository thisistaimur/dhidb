# Contributing and releases

Install the development environment and run the checks locally:

```bash
python -m pip install -e ".[test,docs]"
ruff check src tests
pytest
python -m build
jupyter-book build docs
```

## Versioning

The CI workflow derives a semantic version from Git history. It computes the
candidate version for pull requests and pushes, but creates a tag, GitHub
release, and PyPI distribution only after the test matrix and package build
have succeeded on `main`.

PyPI publication uses GitHub trusted publishing. Configure the `pypi`
environment for this repository on PyPI before enabling the first release.

