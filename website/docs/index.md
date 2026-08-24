---
hide_table_of_contents: true
---

import lightLogo from '@site/static/img/DHIDB_logo_white.png';
import darkLogo from '@site/static/img/DHIDB_logo.png';
import dhi2015 from '@site/static/img/global_dhi_all_components_2015_4rows_highres_2.png';

# 

<div className="hero-logo-wrap">
  <img className="hero-logo hero-logo-light" src={lightLogo} alt="DHIDB logo" />
  <img className="hero-logo hero-logo-dark" src={darkLogo} alt="DHIDB logo" />
</div>

<div className="project-badges">
  <a href="https://pypi.org/project/dhidb/">
    <img src="https://img.shields.io/pypi/v/dhidb.svg?logo=pypi&label=PyPI" alt="Latest PyPI version" />
  </a>
  <a href="https://github.com/thisistaimur/dhidb/actions/workflows/ci-release.yml">
    <img src="https://github.com/thisistaimur/dhidb/actions/workflows/ci-release.yml/badge.svg" alt="CI and release status" />
  </a>
</div>

DHIDB provides direct, read-only access to annual global Dynamic Habitat
Indices at 300 m resolution as a 12-year time series from 2014 to 2025 (continuously updated). Its foundation is the
[Copernicus Land Monitoring Service (CLMS)](https://land.copernicus.eu/),
using CLMS gross primary production and land-surface phenology products. This gives DHIDB a consistent,
global Earth-observation basis for analysing vegetation productivity and
seasonality.

The resulting data remain in a dense TileDB array on public S3-compatible
object storage; the Python package retrieves only the years, variables, and
spatial window requested by the user.

The indices describe three complementary dimensions of vegetation dynamics:

- cumulative productivity (`dhi_cum`),
- the minimum seasonal productivity baseline (`dhi_min`), and
- inter-period variability in gross primary production (`dhi_var`).

```python
from dhidb import DHIProvider

with DHIProvider() as db:
    point = db.query_point(12.37, 51.34, years=range(2014, 2026))
```

:::note
The provider uses the public S3 endpoint and production array defaults
automatically. Public reads do not require credentials.
:::

<figure className="dataset-figure">
  <img src={dhi2015} alt="Global Dynamic Habitat Indices components for 2015" />
  <figcaption>Global DHI components for 2015 at 300 m resolution.</figcaption>
</figure>

## Why TileDB?

The database contains 12 annual layers over a grid of 47,040 by 120,960 cells,
or 68,279,500,800 dense array cells. TileDB exposes this as `(time, y, x)` and
allows small spatial subsets to be read without transferring the full array.
