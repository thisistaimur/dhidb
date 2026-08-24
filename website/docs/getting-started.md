# Getting started

## Install

```bash
pip install dhidb
```

DHIDB supports Python 3.10 and newer. The regular installation includes the
runtime dependencies needed for querying the database:

| Dependency | Version requirement |
|---|---|
| `affine` | `>=2.4` |
| `numpy` | `>=1.26,<3` |
| `pandas` | `>=2.1` |
| `pyproj` | `>=3.6` |
| `rasterio` | `>=1.3` |
| `shapely` | `>=2.0` |
| `tiledb` | `>=0.35,<0.38` |
| `xarray` | `>=2024.1` |

Optional output formats are provided as extras:

```bash
pip install "dhidb[netcdf]"  # adds scipy>=1.11 for NetCDF export
pip install "dhidb[zarr]"    # adds zarr>=2.18 for Zarr export
```

For development and testing, install the test extra (which includes build
tools, pytest, coverage, Ruff, and `scipy>=1.11`):

```bash
python -m pip install -e ".[test]"
```

The extras are feature names, so use `dhidb[netcdf]`, `dhidb[zarr]`, or
`dhidb[test]` rather than a generic `dhidb[dependency]` extra.

## Connect to public S3 storage

Public reads use unsigned S3 requests. No access key is required.

```python
from dhidb import DHIProvider

db = DHIProvider()
print(db.years)
print(db.variables)
db.close()
```

The provider uses the public endpoint and array defaults, so Python needs no
connection arguments:

```python
from dhidb import DHIProvider

with DHIProvider() as db:
    print(db.metadata)
```

## Choose a query mode

Use the non-batch query for small or moderate AOIs that fit comfortably in
memory. It returns one complete Xarray dataset:

```python
with DHIProvider() as db:
    germany = db.query_bbox(
        bounds=(5.8, 47.2, 15.1, 55.1),
        years=[2020, 2021, 2022],
        variables=["dhi_cum", "dhi_min", "dhi_var"],
    )

print(germany)
```

For a large AOI, use `iter_bbox()` to process one spatial window at a time:

```python
with DHIProvider() as db:
    for batch in db.iter_bbox(
        bounds=(5.8, 47.2, 15.1, 55.1),
        years=range(2014, 2026),
        variables=["dhi_cum", "dhi_min", "dhi_var"],
        batch_shape={"y": 256, "x": 256},
    ):
        process(batch)
```

Each batch contains all selected years and variables for one spatial window.
Only the current batch is held by the loop, so memory use is controlled by
`batch_shape`. Smaller windows may be needed when many years or variables are
selected.

## Manage memory for large queries

The regular `query_bbox()` and `query_polygon()` methods materialize their
complete result as an Xarray dataset. Memory use therefore grows with the
number of selected years, spatial cells, and variables. For a large AOI or a
long time range, use `iter_bbox()` and process one batch at a time:

```python
with DHIProvider() as db:
    for batch in db.iter_bbox(
        bounds=(5.8, 47.2, 15.1, 55.1),
        years=range(2014, 2026),
        variables=["dhi_cum", "dhi_min", "dhi_var"],
        batch_shape={"y": 256, "x": 256},
    ):
        process(batch)
```

`batch_shape` controls the maximum spatial dimensions of each yielded
dataset. Reduce the values when selecting many years or variables, or when
running in a memory-limited environment. The provider also applies a
`max_cells` safety limit to prevent accidental materialization of an
oversized query. Increase it only when the result is known to fit in memory:

```python
with DHIProvider(max_cells=100_000_000) as db:
    result = db.query_bbox(
        bounds=(5.8, 47.2, 15.1, 55.1),
        years=[2020, 2021],
        variables=["dhi_cum"],
    )
```

When the result should be saved rather than held in Python, use
`export_bbox(..., batch_shape=...)`. It writes each batch directly to NetCDF,
Zarr, or COG files and keeps memory bounded by the batch size:

```python
with DHIProvider() as db:
    files = db.export_bbox(
        bounds=(5.8, 47.2, 15.1, 55.1),
        output="exports/germany_dhi",
        format="zarr",  # also: "netcdf" or "cog"
        years=range(2014, 2026),
        variables=["dhi_cum", "dhi_min", "dhi_var", "valid_count"],
        batch_shape={"y": 256, "x": 256},
    )

print(f"Wrote {len(files)} batch files")
```

With `batch_shape` set, the exporter writes one file or store per spatial
batch. Use `format="cog"` for multiband GeoTIFF output or `format="netcdf"`
for NetCDF files. Install the corresponding optional dependencies before
exporting: `pip install "dhidb[zarr]"` or `pip install "dhidb[netcdf]"`.

## Save a dataset

For a moderate AOI, save the complete Xarray result directly:

```python
with DHIProvider() as db:
    data = db.query_bbox(
        bounds=(5.8, 47.2, 15.1, 55.1),
        years=[2020, 2021],
        variables=["dhi_cum", "dhi_min", "dhi_var"],
    )

data.to_netcdf("germany_dhi.nc")  # install with: pip install dhidb[netcdf]
# Optional: data.to_zarr("germany_dhi.zarr")  # install with: pip install dhidb[zarr]
```

For large AOIs, write results directly from the streaming exporter instead
of collecting batches in Python:

```python
with DHIProvider() as db:
    files = db.export_bbox(
        bounds=(5.8, 47.2, 15.1, 55.1),
        output="exports/germany",
        format="zarr",  # "netcdf", "zarr", or "cog"
        years=range(2014, 2026),
        variables=["dhi_cum", "dhi_min", "dhi_var"],
        batch_shape={"y": 256, "x": 256},
    )
```

With no `batch_shape`, NetCDF and Zarr create one complete output, while COG
creates one multiband GeoTIFF per year. With `batch_shape`, outputs are
spatially sharded: NetCDF/Zarr create one file or store per batch, and COG
creates one multiband GeoTIFF per batch and year. COG bands correspond to the
selected variables and preserve the DHIDB CRS and affine transform. Install
NetCDF support with `pip install dhidb[netcdf]` and Zarr support with
`pip install dhidb[zarr]`.

## Query safety

The default client refuses a request containing more than 50 million
space-time cells. This protects laptops from accidentally materializing a
global array. Raise the limit deliberately when appropriate:

```python
db = DHIProvider(max_cells=100_000_000)
```
