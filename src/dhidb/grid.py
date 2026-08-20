"""Grid metadata and spatial indexing helpers."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any

import numpy as np
from affine import Affine
from pyproj import CRS, Transformer
from rasterio.windows import Window, from_bounds
from rasterio.windows import transform as window_transform


@dataclass(frozen=True)
class Grid:
    """Spatial grid stored in the TileDB array metadata."""

    width: int
    height: int
    transform: tuple[float, float, float, float, float, float]
    crs_wkt: str

    @classmethod
    def from_metadata(cls, value: str | bytes | dict[str, Any]) -> Grid:
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        if isinstance(value, str):
            value = json.loads(value)
        return cls(
            width=int(value["width"]),
            height=int(value["height"]),
            transform=tuple(float(v) for v in value["transform"]),
            crs_wkt=str(value["crs_wkt"]),
        )

    @property
    def affine(self) -> Affine:
        return Affine(*self.transform)

    @property
    def crs(self) -> CRS:
        return CRS.from_wkt(self.crs_wkt)

    def transform_bounds(
        self,
        bounds: tuple[float, float, float, float],
        source_crs: str | CRS,
    ) -> tuple[float, float, float, float]:
        transformer = Transformer.from_crs(source_crs, self.crs, always_xy=True)
        return transformer.transform_bounds(*bounds, densify_pts=21)

    def window_for_bounds(
        self,
        bounds: tuple[float, float, float, float],
    ) -> tuple[int, int, int, int]:
        raw = from_bounds(*bounds, transform=self.affine)
        col0 = max(0, int(math.floor(raw.col_off)))
        row0 = max(0, int(math.floor(raw.row_off)))
        col1 = min(self.width, int(math.ceil(raw.col_off + raw.width)))
        row1 = min(self.height, int(math.ceil(raw.row_off + raw.height)))
        if row1 <= row0 or col1 <= col0:
            raise ValueError("The requested area does not overlap the DHIDB grid.")
        return row0, row1, col0, col1

    def coordinates(
        self, row0: int, row1: int, col0: int, col1: int
    ) -> tuple[np.ndarray, np.ndarray]:
        affine = self.affine
        if affine.b != 0 or affine.d != 0:
            raise NotImplementedError("Rotated grids are not supported by this client.")
        x = affine.c + (np.arange(col0, col1, dtype=np.float64) + 0.5) * affine.a
        y = affine.f + (np.arange(row0, row1, dtype=np.float64) + 0.5) * affine.e
        return x, y

    def subset_transform(self, row0: int, col0: int) -> Affine:
        return window_transform(Window(col0, row0, 1, 1), self.affine)
