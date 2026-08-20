# Quality information

The database retains observation counts alongside the DHI components so that
users can evaluate temporal support for each pixel.

`observed_count` records how many 10-day GPP scenes were present.
`valid_count` records how many contributed after source-quality screening.
`qflag_any_count` and `qflag_rejected_count` summarize the original
Copernicus QFLAG observations.

For annual products, a maximum `valid_count` of 36 is expected. The TileDB
fill value for an unwritten `uint16` cell is 65,535; clients should not
interpret that value as an observation count. Query only production-complete
years and use finite DHI values together with plausible count values when
validating an analysis.

