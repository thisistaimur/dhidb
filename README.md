# dhidb <a href='https://thisistaimur.github.io/dhidb/'><img src='https://raw.githubusercontent.com/thisistaimur/dhidb/main/assetts/DHIDB_logo_white.png' align="right" height="200" /></a>

[![PyPI version](https://img.shields.io/pypi/v/dhidb.svg?logo=pypi&label=PyPI)](https://pypi.org/project/dhidb/)
[![CI and release](https://github.com/thisistaimur/dhidb/actions/workflows/ci-release.yml/badge.svg)](https://github.com/thisistaimur/dhidb/actions/workflows/ci-release.yml)

`dhidb` provides read-only Python access to a global 300 m, 12-year
(2014-2025) Dynamic Habitat Indices time series stored as a dense TileDB array
on public S3-compatible object storage. It supports point, bounding-box, and
polygon queries without first downloading the complete database.

DHIs are widely used in spatial ecology as interpretable predictors of habitat
quality and vegetation dynamics, including covariates in species distribution
models (SDMs) and biodiversity assessments.


## Installation

```bash
pip install dhidb
```

For development:

```bash
python -m pip install -e ".[test]"
```

## Requirements and optional dependencies

DHIDB requires Python 3.10 or newer. The runtime dependencies and the
compatibility ranges published by the package are:

| Dependency | Supported version range |
|---|---|
| `affine` | `>=2.4` |
| `numpy` | `>=1.26,<3` |
| `pandas` | `>=2.1` |
| `pyproj` | `>=3.6` |
| `rasterio` | `>=1.3` |
| `shapely` | `>=2.0` |
| `tiledb` | `>=0.35,<0.38` |
| `xarray` | `>=2024.1` |

Optional features are installed with package extras. There is no generic
`dhidb[dependency]` extra; use the feature-specific extra you need:

| Extra | Install command | Adds |
|---|---|---|
| `netcdf` | `pip install "dhidb[netcdf]"` | `scipy>=1.11` for NetCDF export |
| `zarr` | `pip install "dhidb[zarr]"` | `zarr>=2.18` for Zarr export |
| `test` | `pip install "dhidb[test]"` | build, pytest, coverage, Ruff, and SciPy tooling |

For local development and testing:

```bash
python -m pip install -e ".[test,netcdf,zarr]"
```

The documentation website has its own Node.js dependencies in
[`website/package.json`](website/package.json); they are not part of the
Python package extras.

## Quick start

```python
from dhidb import DHIProvider

with DHIProvider() as db:
    print(db.years)
    print(db.variables)

    germany = db.query_bbox(
        bounds=(5.8, 47.2, 15.1, 55.1),
        years=[2020, 2021, 2022],
        variables=["dhi_cum", "dhi_min", "dhi_var", "valid_count"],
    )
```

## Documentation

The Docusaurus website source is in [`website/`](website/). Build it locally
with:

```bash
npm --prefix website install
npm --prefix website run start
```

## Data variables

| Variable | Meaning | Unit |
|---|---|---|
| `dhi_cum` | Cumulative productivity from LSP TPROD | PPI integral (`m2 m-2 day`) |
| `dhi_min` | Minimum seasonal productivity baseline from LSP MINV | PPI (`m2 m-2`) |
| `dhi_var` | Inter-period GPP coefficient of variation | dimensionless |
| `dhi_combined` | Normalized combined DHI, where available | dimensionless |
| `observed_count` | Number of available 10-day observations | scenes |
| `valid_count` | Number of accepted 10-day observations | scenes |
| `qflag_any_count` | Observations carrying any source quality flag | scenes |
| `qflag_rejected_count` | Observations rejected by quality filtering | scenes |

## License

MIT
