# Global habitat dynamics, queried where you need them

```{image} _static/DHIDB_logo.png
:alt: DHIDB logo
:class: hero-logo
:width: 760px
:align: center
```

DHIDB provides direct, read-only access to annual global Dynamic Habitat
Indices at 300 m resolution. The data remain in a dense TileDB array on public
S3-compatible object storage; the Python package retrieves only the years,
variables, and spatial window requested by the user.

The indices describe three complementary dimensions of vegetation dynamics:

- cumulative productivity (`dhi_cum`),
- the minimum seasonal productivity baseline (`dhi_min`), and
- inter-period variability in gross primary production (`dhi_var`).

```python
from dhidb import DHIProvider

with DHIProvider() as db:
    point = db.query_point(12.37, 51.34, years=range(2014, 2026))
```

:::{important}
The provider uses the public QAS endpoint and production array defaults
automatically. Public reads do not require credentials.
:::

## Why TileDB?

The database contains 12 annual layers over a grid of 47,040 by 120,960 cells,
or 68,279,500,800 dense array cells. TileDB exposes this as `(time, y, x)` and
allows small spatial subsets to be read without transferring the full array.
