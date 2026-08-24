# Quality information

The database retains observation counts alongside the DHI components so that
users can evaluate temporal support for each pixel.

## What the quality layers mean

`observed_count` records how many 10-day GPP scenes were present.
`valid_count` records how many contributed after source-quality screening.
`qflag_any_count` and `qflag_rejected_count` summarize the original
Copernicus QFLAG observations.

| Attribute | Type | Meaning |
|---|---|---|
| `observed_count` | `uint16` | Finite GPP scenes available before optional QFLAG filtering |
| `valid_count` | `uint16` | Scenes used in the GPP time-series calculations |
| `qflag_any_count` | `uint16` | Finite scenes carrying a non-zero source QFLAG |
| `qflag_rejected_count` | `uint16` | Finite scenes rejected when optional QFLAG masking is enabled |

The quality attributes are provenance and data-support summaries, not
uncertainty estimates and not error bars for the DHI values. In the default
production configuration, QFLAG is retained as categorical information and
is not used as a hard production mask. This means `valid_count` can equal
`observed_count` even when QFLAG information is present.

For annual products, a maximum `valid_count` of 36 is expected. The TileDB
fill value for an unwritten `uint16` cell is 65,535; clients should not
interpret that value as an observation count. Query only production-complete
years and use finite DHI values together with plausible count values when
validating an analysis.

Floating-point DHI attributes use `NaN` for pixels with no finite input
observations. A count of zero and non-finite DHI values indicate that no
usable input supported the calculation. For robust filtering, require finite
values for the selected DHI variable and constrain counts to the expected
range for the product rather than testing only for non-zero values.
