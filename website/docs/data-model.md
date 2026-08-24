# Data model

DHIDB v1 is a dense TileDB array with dimensions `(time, y, x)`. The array
stores annual global layers on the CLMS 300 m raster grid. TileDB Embedded
reads only the selected ranges, so a point, bounding-box, or polygon query
does not require downloading the global archive.

| Dimension | Size | Meaning |
|---|---:|---|
| `time` | 12 | Annual layers from 2014 through 2025 |
| `y` | 47,040 | Global raster rows |
| `x` | 120,960 | Global raster columns |

Each annual layer contains 5,689,958,400 grid cells. The complete logical
array contains 68,279,500,800 cells before compression and exclusion of
unwritten fragments.

The spatial dimensions use zero-based raster row and column indices. The
array domain is `time=0..11`, `y=0..47039`, and `x=0..120959` for the current
2014--2025 build. The mapping from a time index to a calendar year is stored
in the array metadata as `time_index`; clients should use `db.years` rather
than assuming that every future build has the same labels.

## DHI variables

The three primary variables describe complementary aspects of vegetation
dynamics. Let `p` be a pixel and `y` a year. The source GPP time series is
denoted by `g(p, y, d)`, where `d` indexes the available 10-day scenes.

### Cumulative productivity: `dhi_cum`

Where the annual LSP product is available, `dhi_cum` is the sum of the two
seasonal LSP total-productivity values:

~~~text
dhi_cum(p, y) = TPROD(p, y, season 1) + TPROD(p, y, season 2)
~~~

`TPROD` is the growing-season integral of PPI between the detected start and
end of a season. It is an LSP seasonal productivity summary, not a direct sum
of the 10-day GPP scenes. Its stored unit is **m2 m-2 day**, as documented for the
PPI-integral representation. If the LSP values are unavailable, the
production code can use the finite GPP time series as a cumulative fallback.

### Minimum productivity: `dhi_min`

`dhi_min` is the lower seasonal productivity level across the two LSP
seasons:

~~~text
dhi_min(p, y) = min(MINV(p, y, season 1), MINV(p, y, season 2))
~~~

`MINV` is the average of the PPI minima on the left and right sides of the
season. The stored unit is **m2 m-2**. This is an LSP-derived seasonal
minimum-value baseline proxy, not the pixel-wise minimum of the 10-day GPP
scenes. A finite GPP minimum is available as a fallback when LSP values cannot
be used.

### Temporal variability: `dhi_var`

`dhi_var` is calculated from the accepted finite 10-day GPP values. Let
`V(p, y)` be the valid scene indices and `mean_g(p, y)` their arithmetic mean:

~~~text
mean_g(p, y) = sum(g(p, y, d) for d in V(p, y)) / count(V(p, y))

dhi_var(p, y) =
  population_standard_deviation(g(p, y, d) for d in V(p, y)) / mean_g(p, y)
~~~

This is a coefficient of variation and is **dimensionless**. It represents
relative intra-annual variation in GPP; it is not a variance in GPP units.

## Variables

| Variable | Definition | Unit |
|---|---|---|
| `dhi_cum` | Sum of LSP TPROD over two growing seasons | PPI integral (`m2 m-2 day`) |
| `dhi_min` | Minimum of scaled LSP MINV over two growing seasons | PPI (`m2 m-2`) |
| `dhi_var` | Coefficient of variation of accepted 10-day GPP | dimensionless |
| `dhi_combined` | Geometric mean of normalized component layers | dimensionless |
| `observed_count` | Available GPP observations | scenes |
| `valid_count` | Accepted GPP observations | scenes |
| `qflag_any_count` | Observations carrying any source QFLAG | scenes |
| `qflag_rejected_count` | Rejected observations | scenes |

`dhi_cum` and `dhi_min` summarize the smoothed Plant Phenology Index
trajectory represented by Copernicus LSP. They are not direct annual GPP sums
or minima. `dhi_var` is calculated from the 10-day GPP time series.

The count attributes are stored as `uint16`; the DHI attributes are stored as
`float32`. Pixels with no finite observations use `NaN` for floating-point
DHI attributes and zero for the count attributes. An unwritten TileDB cell
can instead expose the uint16 fill value `65,535`, so consumers should check
for plausible counts and finite DHI values rather than treating every count
as an observation.

## Combined score

The schema includes `dhi_combined`, but the current production archive does
not populate it unless global normalization bounds are supplied. For
components `X_k`, with lower and upper bounds `L_k` and `U_k`, the
planned normalization is:

~~~text
Z(k) = clip((X(k) - L(k)) / (U(k) - L(k)), 0, 1)
dhi_combined = (Z(cumulative) * Z(minimum) * Z(variation)) ** (1 / 3)
~~~

This remains disabled by default because tile-local normalization would make
values incomparable between locations and years. Treat `dhi_combined` as
unavailable in v1 unless the dataset metadata explicitly provides the
normalization bounds.

## TileDB storage layout

The array is **dense**, not sparse. Its dimensions, tile extents, and stored
attributes are fixed by the schema:

| Schema element | Configuration |
|---|---|
| Dimensions | `time`, `y`, `x` |
| Dimension domains | `0..11`, `0..47039`, `0..120959` in the current build |
| Tile extents | `time=1`, `y=1024`, `x=1024` |
| Spatial processing tiles | 1,024 x 1,024 cells, approximately 307.2 x 307.2 km on the 300 m grid |
| DHI attribute type | `float32` |
| Count attribute type | `uint16` |
| Compression | Zstandard on dimensions and attributes |
| Cell order | Row-major |

One annual layer therefore has 119 tiles across and 46 tiles down, or 5,474
spatial tiles. The one-cell time tile aligns storage with the dominant access
pattern: selected annual layers over a spatial window. The physical size on
disk is smaller than the logical cell count because TileDB stores compressed
attribute chunks and only materialized fragments.

The array metadata records the grid width and height, affine transform, CRS
WKT, spatial tile height and width, and the `time_index` mapping. These
metadata are required to convert array coordinates into geospatial outputs.

## Reproducibility note

The source LSP value layers contain product-specific scaling information.
Before treating `dhi_min` as a calibrated physical quantity, users should
check the release metadata and scale/offset handling for the exact source
version. The ecological interpretation of `MINV` as a seasonal baseline proxy
is separate from this numerical calibration issue.
