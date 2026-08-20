# Data model

DHIDB v1 is a dense TileDB array with dimensions `(time, y, x)`.

| Dimension | Size | Meaning |
|---|---:|---|
| `time` | 12 | Annual layers from 2014 through 2025 |
| `y` | 47,040 | Global raster rows |
| `x` | 120,960 | Global raster columns |

Each annual layer contains 5,689,958,400 grid cells. The complete logical
array contains 68,279,500,800 cells before compression and exclusion of
unwritten fragments.

## Variables

| Variable | Definition | Unit |
|---|---|---|
| `dhi_cum` | Sum of LSP TPROD over two growing seasons | PPI integral (`m2 m-2 day`) |
| `dhi_min` | Minimum of scaled LSP MINV over two growing seasons | PPI (`m2 m-2`) |
| `dhi_var` | Coefficient of variation of accepted 10-day GPP | dimensionless |
| `dhi_combined` | Sum of normalized component layers | dimensionless |
| `observed_count` | Available GPP observations | scenes |
| `valid_count` | Accepted GPP observations | scenes |
| `qflag_any_count` | Observations carrying any source QFLAG | scenes |
| `qflag_rejected_count` | Rejected observations | scenes |

`dhi_cum` and `dhi_min` summarize the smoothed Plant Phenology Index
trajectory represented by Copernicus LSP. They are not direct annual GPP sums
or minima. `dhi_var` is calculated from the 10-day GPP time series.

