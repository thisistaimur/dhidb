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

