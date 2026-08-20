from __future__ import annotations

import json

import numpy as np
import pytest
import rasterio
import tiledb


@pytest.fixture()
def sample_array(tmp_path):
    uri = str(tmp_path / "sample_dhidb")
    domain = tiledb.Domain(
        tiledb.Dim(name="time", domain=(0, 1), tile=1, dtype=np.int32),
        tiledb.Dim(name="y", domain=(0, 2), tile=2, dtype=np.int32),
        tiledb.Dim(name="x", domain=(0, 3), tile=2, dtype=np.int32),
    )
    attrs = [
        tiledb.Attr(name="dhi_cum", dtype=np.float32),
        tiledb.Attr(name="dhi_min", dtype=np.float32),
        tiledb.Attr(name="dhi_var", dtype=np.float32),
        tiledb.Attr(name="valid_count", dtype=np.uint16),
    ]
    tiledb.Array.create(uri, tiledb.ArraySchema(domain=domain, attrs=attrs, sparse=False))

    values = np.arange(24, dtype=np.float32).reshape(2, 3, 4)
    with tiledb.open(uri, "w") as array:
        array[0:2, 0:3, 0:4] = {
            "dhi_cum": values,
            "dhi_min": values * np.float32(0.001),
            "dhi_var": values / np.float32(10),
            "valid_count": np.full((2, 3, 4), 36, dtype=np.uint16),
        }
        array.meta["grid"] = json.dumps(
            {
                "width": 4,
                "height": 3,
                "transform": [1.0, 0.0, -180.0, 0.0, -1.0, 90.0],
                "crs_wkt": rasterio.crs.CRS.from_epsg(4326).to_wkt(),
            }
        )
        array.meta["time_index"] = json.dumps({"2020": 0, "2021": 1})
    return uri

