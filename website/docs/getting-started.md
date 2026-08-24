# Getting started

## Install

```bash
pip install dhidb
```

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

## Save a dataset

For a moderate AOI, save the complete Xarray result directly:

```python
with DHIProvider() as db:
    data = db.query_bbox(
        bounds=(5.8, 47.2, 15.1, 55.1),
        years=[2020, 2021],
        variables=["dhi_cum", "dhi_min", "dhi_var"],
    )

data.to_netcdf("germany_dhi.nc")
# Optional: data.to_zarr("germany_dhi.zarr")
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
Zarr support with `pip install dhidb[zarr]`.

## Query safety

The default client refuses a request containing more than 50 million
space-time cells. This protects laptops from accidentally materializing a
global array. Raise the limit deliberately when appropriate:

```python
db = DHIProvider(max_cells=100_000_000)
```
