---
id: api
title: Python API
sidebar_label: Python API
---

The public API is intentionally small: one read-only provider exposes point,
bounding-box, and polygon queries over the TileDB array.

## `DHIProvider`

```python
from dhidb import DHIProvider

with DHIProvider() as db:
    print(db.years)
    print(db.variables)
```

### Constructor

```python
DHIProvider(
    array_uri=None,
    endpoint_url=None,
    *,
    region=None,
    max_cells=None,
    config=None,
    tiledb_config=None,
)
```

The default URI is the public DHIDB array. Set `array_uri` and
`endpoint_url` to use another compatible deployment. `max_cells` protects
local machines from accidentally materializing very large queries.

The provider opens the array in read-only mode through TileDB Embedded. It
uses the array's stored `time_index` metadata to map calendar years to TileDB
time positions and reads the stored affine transform and CRS metadata when
constructing spatial results. The default endpoint and array URI can be
overridden through the constructor or the `DHIDB_ENDPOINT_URL` and
`DHIDB_ARRAY_URI` environment variables.

### Properties

- `years` returns the available annual labels.
- `variables` returns the TileDB attributes.
- `grid` returns the spatial grid definition.
- `metadata` returns the array metadata.

### Query methods

- `query_point(longitude, latitude, years=None, variables=None, crs="EPSG:4326")`
  returns a pandas `DataFrame`.
- `query_bbox(bounds, years=None, variables=None, crs="EPSG:4326")` returns
  an xarray `Dataset`.
- `iter_bbox(bounds, years=None, variables=None, crs="EPSG:4326",
  batch_shape={"y": 256, "x": 256})` yields bounded xarray `Dataset` batches.
- `export_bbox(bounds, output, format="zarr", ..., batch_shape=...)` streams
  batches directly to NetCDF, Zarr, or COG files.
- `query_polygon(geometry, years=None, variables=None, crs="EPSG:4326",
  all_touched=False)` returns a masked xarray `Dataset`.

### Query examples

#### Point time series

`query_point()` returns a pandas `DataFrame` with one row per requested year:

```python
with DHIProvider() as db:
    leipzig = db.query_point(
        longitude=12.3731,
        latitude=51.3397,
        years=range(2014, 2026),
        variables=["dhi_cum", "dhi_min", "dhi_var", "valid_count"],
    )

print(leipzig[["dhi_cum", "dhi_min", "dhi_var"]])
```

#### Bounding-box subset

`query_bbox()` returns an Xarray `Dataset` with `(time, y, x)` dimensions:

```python
with DHIProvider() as db:
    germany = db.query_bbox(
        bounds=(5.8, 47.2, 15.1, 55.1),
        years=[2020, 2021, 2022],
        variables=["dhi_cum", "dhi_min", "dhi_var", "valid_count"],
    )

print(germany)
germany.to_netcdf("germany_dhi.nc")
```

#### Polygon subset

`query_polygon()` accepts a GeoJSON path, GeoJSON mapping, Shapely geometry,
or object implementing `__geo_interface__`. Pixels outside the polygon are
returned as missing values:

```python
with DHIProvider() as db:
    protected_area = db.query_polygon(
        "study_area.geojson",
        years=2024,
        variables=["dhi_cum", "dhi_min", "dhi_var"],
        crs="EPSG:4326",
        all_touched=True,
    )

print(protected_area.dhi_cum)
```

For a large polygon, stream its bounding box with `iter_bbox()` and apply a
mask per batch as shown in the [query recipes](./queries#streaming-a-large-polygon).

#### Projected coordinates

Bounds and points can be supplied in another coordinate reference system by
setting `crs`:

```python
with DHIProvider() as db:
    projected = db.query_bbox(
        bounds=(300000, 5600000, 400000, 5700000),
        crs="EPSG:25833",
        years=2024,
        variables=["dhi_cum"],
    )
```

All query methods read only the requested spatial and temporal subset.
The returned DHI values retain their native units: `dhi_cum` is `m2 m-2 day`,
`dhi_min` is `m2 m-2`, and `dhi_var` and `dhi_combined` are dimensionless.
Count variables are numbers of scenes. The API does not rescale these values
or convert `dhi_combined` into an alternative score.

### Streaming large bounding boxes

`query_bbox()` materializes its complete result in memory. For large areas,
use `iter_bbox()` to read bounded spatial windows one at a time:

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

The iterator yields Xarray datasets with the same `(time, y, x)` dimensions
and metadata as `query_bbox()`. Windows are read in row-major order and the
full bounding box is never materialized at once. The provider's `max_cells`
limit applies to each batch; choose a smaller batch shape if a multi-year
batch exceeds that limit. Batches are released normally after each loop
iteration, so callers should process or persist them before requesting the
next batch.

### Streaming exports

Use `export_bbox()` when the result should be persisted. With no
`batch_shape`, NetCDF/Zarr produce one complete output and COG produces one
multiband raster per year:

```python
with DHIProvider() as db:
    paths = db.export_bbox(
        bounds=(5.8, 47.2, 15.1, 55.1),
        output="exports/germany",
        format="zarr",
        years=range(2014, 2026),
        variables=["dhi_cum", "dhi_min", "dhi_var"],
    )
```

Supported formats are `"netcdf"`, `"zarr"`, and `"cog"` (with `"nc"` and
`"tif"` aliases). Without `batch_shape`, NetCDF writes `data.nc`, Zarr
writes `data.zarr`, and COG writes `{year}.tif`. COG bands correspond to the
selected variables, are stored as float32, and include band descriptions.
With `batch_shape`, NetCDF/Zarr write one `batch_*.nc`/`batch_*.zarr` per
spatial batch and COG writes one `batch_*_{year}.tif` per batch and year. The
method returns the paths written. Zarr export requires the optional `zarr`
dependency (`pip install dhidb[zarr]`). NetCDF export requires a backend such
as SciPy (`pip install dhidb[netcdf]`).
