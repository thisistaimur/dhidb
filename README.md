<p align="center">
  <img src="https://raw.githubusercontent.com/thisistaimur/dhidb/main/assetts/DHIDB_logo_white.png" alt="DHIDB" width="720">
</p>

# dhidb

`dhidb` provides read-only Python access to the global 300 m Dynamic Habitat
Indices database stored as a dense TileDB array on public S3-compatible object
storage. It supports point, bounding-box, and polygon queries without first
downloading the complete database.


## Installation

```bash
pip install dhidb
```

For development:

```bash
python -m pip install -e ".[test,docs]"
```

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

The Jupyter Book source is in [`docs/`](docs/). Build it locally with:

```bash
jupyter-book build docs
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
