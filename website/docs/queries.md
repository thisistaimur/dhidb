# Query recipes

## Point time series

```python
with DHIProvider() as db:
    leipzig = db.query_point(
        longitude=12.3731,
        latitude=51.3397,
        years=range(2014, 2026),
        variables=["dhi_cum", "dhi_min", "dhi_var", "valid_count"],
    )
```

The result is a `pandas.DataFrame` indexed by year.

## Bounding box

```python
with DHIProvider() as db:
    germany = db.query_bbox(
        bounds=(5.8, 47.2, 15.1, 55.1),
        years=[2020, 2021, 2022],
        variables=["dhi_cum", "dhi_min", "dhi_var"],
    )
```

The result is an `xarray.Dataset` with `(time, y, x)` dimensions and CRS and
affine-transform metadata.

## Streaming a large bounding box

For a large AOI, avoid materializing the entire result with `query_bbox()`.
`iter_bbox()` yields spatial windows lazily while retaining the requested
years in each batch:

```python
with DHIProvider() as db:
    for batch in db.iter_bbox(
        bounds=(5.8, 47.2, 15.1, 55.1),
        years=range(2014, 2026),
        variables=["dhi_cum", "dhi_min", "dhi_var", "valid_count"],
        batch_shape={"y": 256, "x": 256},
    ):
        # Write, aggregate, or pass this bounded Dataset to a model.
        process(batch)
```

Each batch contains at most the requested `y` by `x` cells and all selected
time steps. Reduce the batch dimensions when the selected years and variables
would exceed the provider's `max_cells` limit.

## Persisting streamed batches

The same streaming path can write results directly to disk:

```python
with DHIProvider() as db:
    files = db.export_bbox(
        bounds=(5.8, 47.2, 15.1, 55.1),
        output="exports/germany",
        format="cog",
        years=[2020, 2021, 2022],
        variables=["dhi_cum", "dhi_min", "dhi_var"],
        batch_shape={"y": 512, "x": 512},
    )
```

With `batch_shape` set, NetCDF and Zarr create one output per spatial batch,
while COG creates one multiband raster per spatial batch and year. Without
`batch_shape`, NetCDF/Zarr create one complete output and COG creates one
multiband raster per year. COG bands correspond to the selected variables
and preserve the DHIDB CRS and affine transform. This layout keeps memory
bounded in batch mode and makes individual files easy to process in parallel.

## Polygon

Pass a Shapely geometry, GeoJSON mapping, object implementing
`__geo_interface__`, or path to a GeoJSON file:

```python
with DHIProvider() as db:
    clipped = db.query_polygon(
        "study_area.geojson",
        years=2024,
        variables=["dhi_cum", "dhi_min", "dhi_var"],
        crs="EPSG:4326",
    )
```

Pixels outside the polygon are represented as missing values. Set
`all_touched=True` to include every grid cell touched by the polygon.

## A projected query

The input bounds or geometry need not be in longitude/latitude:

```python
subset = db.query_bbox(
    bounds=(300000, 5600000, 400000, 5700000),
    crs="EPSG:25833",
    years=2024,
)
```
