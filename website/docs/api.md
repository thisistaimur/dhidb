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
- `query_polygon(geometry, years=None, variables=None, crs="EPSG:4326",
  all_touched=False)` returns a masked xarray `Dataset`.

All query methods read only the requested spatial and temporal subset.
The returned DHI values retain their native units: `dhi_cum` is `m2 m-2 day`,
`dhi_min` is `m2 m-2`, and `dhi_var` and `dhi_combined` are dimensionless.
Count variables are numbers of scenes. The API does not rescale these values
or convert `dhi_combined` into an alternative score.
