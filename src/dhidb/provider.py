"""Read-only TileDB provider for Dynamic Habitat Indices."""

from __future__ import annotations

import importlib.util
import json
import os
from collections.abc import Iterable, Iterator, Mapping, Sequence
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import numpy as np
import pandas as pd
import xarray as xr
from pyproj import CRS, Transformer
from rasterio.features import geometry_mask
from shapely.geometry import GeometryCollection, shape
from shapely.ops import transform as transform_geometry
from shapely.ops import unary_union

from .config import DEFAULT_YEARS, DHIConfig
from .grid import Grid

DEFAULT_VARIABLES = ("dhi_cum", "dhi_min", "dhi_var", "valid_count")

VARIABLE_METADATA = {
    "dhi_cum": {
        "long_name": "cumulative productivity DHI",
        "units": "m2 m-2 day",
    },
    "dhi_min": {
        "long_name": "minimum seasonal productivity DHI",
        "units": "m2 m-2",
    },
    "dhi_var": {
        "long_name": "inter-period GPP coefficient of variation",
        "units": "1",
    },
    "dhi_combined": {"long_name": "combined normalized DHI", "units": "1"},
    "observed_count": {"long_name": "available observations", "units": "scenes"},
    "valid_count": {"long_name": "accepted observations", "units": "scenes"},
    "qflag_any_count": {
        "long_name": "observations carrying any quality flag",
        "units": "scenes",
    },
    "qflag_rejected_count": {
        "long_name": "observations rejected by quality filtering",
        "units": "scenes",
    },
}


def _normalise_endpoint(endpoint_url: str) -> tuple[str, str]:
    parsed = urlparse(endpoint_url if "://" in endpoint_url else f"https://{endpoint_url}")
    if not parsed.hostname:
        raise ValueError(f"Invalid S3 endpoint URL: {endpoint_url!r}")
    host = parsed.netloc
    scheme = parsed.scheme or "https"
    return host, scheme


def _tiledb_context(config: DHIConfig):
    # The public endpoint currently rejects optional AWS checksum headers.
    # Keep this internal until it supports them; explicit user settings win.
    os.environ.setdefault("AWS_RESPONSE_CHECKSUM_VALIDATION", "when_required")
    os.environ.setdefault("AWS_REQUEST_CHECKSUM_CALCULATION", "when_required")

    import tiledb

    threads = str(min(os.cpu_count() or 4, 8))
    values = {
        "sm.compute_concurrency_level": threads,
        "sm.io_concurrency_level": threads,
        "sm.tile_cache_size": str(256 * 1024**2),
        "py.init_buffer_bytes": str(64 * 1024**2),
    }
    if config.array_uri.startswith("s3://"):
        values.update(
            {
                "vfs.s3.region": config.region,
                "vfs.s3.use_virtual_addressing": (
                    "true" if config.use_virtual_addressing else "false"
                ),
                "vfs.s3.no_sign_request": "true" if config.anonymous else "false",
            }
        )
        if config.endpoint_url:
            host, scheme = _normalise_endpoint(config.endpoint_url)
            values["vfs.s3.endpoint_override"] = host
            values["vfs.s3.scheme"] = scheme
    values.update({str(k): str(v) for k, v in config.tiledb_config.items()})
    return tiledb.Ctx(values)


class DHIProvider:
    """Query the public DHIDB TileDB array.

    The provider is strictly read-only. It reuses one TileDB array handle to
    avoid repeated object-storage metadata requests and can be used as a
    context manager.
    """

    def __init__(
        self,
        array_uri: str | None = None,
        endpoint_url: str | None = None,
        *,
        region: str | None = None,
        max_cells: int | None = None,
        config: DHIConfig | None = None,
        tiledb_config: dict[str, str] | None = None,
    ) -> None:
        base = config or DHIConfig()
        self.config = DHIConfig(
            array_uri=array_uri or base.array_uri,
            endpoint_url=endpoint_url if endpoint_url is not None else base.endpoint_url,
            region=region or base.region,
            use_virtual_addressing=base.use_virtual_addressing,
            anonymous=base.anonymous,
            max_cells=max_cells if max_cells is not None else base.max_cells,
            tiledb_config=tiledb_config or base.tiledb_config,
        )
        self._ctx = _tiledb_context(self.config)
        self._array = None
        self._grid: Grid | None = None
        self._years: tuple[int, ...] | None = None

    def _get_array(self):
        import tiledb

        if self._array is None or not self._array.isopen:
            self._array = tiledb.open(self.config.array_uri, mode="r", ctx=self._ctx)
        return self._array

    @property
    def grid(self) -> Grid:
        if self._grid is None:
            array = self._get_array()
            if "grid" not in array.meta:
                raise RuntimeError("The TileDB array does not contain required 'grid' metadata.")
            self._grid = Grid.from_metadata(array.meta["grid"])
        return self._grid

    @property
    def variables(self) -> tuple[str, ...]:
        schema = self._get_array().schema
        return tuple(schema.attr(i).name for i in range(schema.nattr))

    @property
    def years(self) -> tuple[int, ...]:
        if self._years is None:
            array = self._get_array()
            if "time_index" in array.meta:
                raw = array.meta["time_index"]
                if isinstance(raw, bytes):
                    raw = raw.decode("utf-8")
                mapping = json.loads(raw)
                self._years = tuple(
                    int(label) for label, _ in sorted(mapping.items(), key=lambda item: item[1])
                )
            else:
                time_size = int(array.schema.domain.dim("time").domain[1]) + 1
                if time_size > len(DEFAULT_YEARS):
                    raise RuntimeError(
                        "The array has no time_index metadata and exceeds the known v1 time axis."
                    )
                self._years = DEFAULT_YEARS[:time_size]
        return self._years

    @property
    def metadata(self) -> dict[str, Any]:
        array = self._get_array()
        return {key: array.meta[key] for key in array.meta}

    def _validate_variables(self, variables: Sequence[str] | None) -> tuple[str, ...]:
        selected = tuple(variables or DEFAULT_VARIABLES)
        unknown = sorted(set(selected).difference(self.variables))
        if unknown:
            raise ValueError(
                f"Unknown variables: {', '.join(unknown)}. Available: {', '.join(self.variables)}"
            )
        return selected

    def _year_positions(self, years: int | Iterable[int] | None) -> tuple[list[int], list[int]]:
        selected = list(
            self.years if years is None else ([years] if isinstance(years, int) else years)
        )
        missing = sorted(set(selected).difference(self.years))
        if missing:
            raise ValueError(f"Years not available: {', '.join(map(str, missing))}")
        positions = [self.years.index(int(year)) for year in selected]
        return [int(year) for year in selected], positions

    def _check_size(self, times: int, rows: int, cols: int) -> None:
        cells = times * rows * cols
        if cells > self.config.max_cells:
            raise ValueError(
                f"Query contains {cells:,} cells, above the safety limit of "
                f"{self.config.max_cells:,}. Use a smaller AOI/year range or increase max_cells."
            )

    def _query_window(
        self,
        *,
        row0: int,
        row1: int,
        col0: int,
        col1: int,
        years: int | Iterable[int] | None,
        variables: Sequence[str] | None,
    ) -> xr.Dataset:
        selected_variables = self._validate_variables(variables)
        year_labels, positions = self._year_positions(years)
        self._check_size(len(positions), row1 - row0, col1 - col0)

        array = self._get_array()
        values: dict[str, list[np.ndarray]] = {name: [] for name in selected_variables}
        for position in positions:
            result = array.query(attrs=list(selected_variables))[
                position : position + 1, row0:row1, col0:col1
            ]
            for name in selected_variables:
                values[name].append(result[name][0])

        x, y = self.grid.coordinates(row0, row1, col0, col1)
        dataset = xr.Dataset(
            {
                name: (("time", "y", "x"), np.stack(chunks, axis=0))
                for name, chunks in values.items()
            },
            coords={"time": np.asarray(year_labels), "y": y, "x": x},
            attrs={
                "title": "Global 300 m Dynamic Habitat Indices",
                "source": self.config.array_uri,
                "crs_wkt": self.grid.crs_wkt,
                "transform": tuple(self.grid.subset_transform(row0, col0))[:6],
            },
        )
        for name in dataset.data_vars:
            dataset[name].attrs.update(VARIABLE_METADATA.get(name, {}))
        return dataset

    def query_bbox(
        self,
        bounds: tuple[float, float, float, float],
        *,
        years: int | Iterable[int] | None = None,
        variables: Sequence[str] | None = None,
        crs: str | CRS = "EPSG:4326",
    ) -> xr.Dataset:
        """Return DHI data intersecting ``(minx, miny, maxx, maxy)``."""

        grid_bounds = self.grid.transform_bounds(bounds, crs)
        row0, row1, col0, col1 = self.grid.window_for_bounds(grid_bounds)
        return self._query_window(
            row0=row0,
            row1=row1,
            col0=col0,
            col1=col1,
            years=years,
            variables=variables,
        )

    def iter_bbox(
        self,
        bounds: tuple[float, float, float, float],
        *,
        years: int | Iterable[int] | None = None,
        variables: Sequence[str] | None = None,
        crs: str | CRS = "EPSG:4326",
        batch_shape: Mapping[str, int] | None = None,
    ) -> Iterator[xr.Dataset]:
        """Yield bounded Xarray batches for a bounding box.

        ``batch_shape`` specifies the maximum number of grid cells per batch
        in the ``y`` and ``x`` dimensions. Batches are read lazily in
        row-major order, so the full bounding box is never materialized at
        once. The existing ``max_cells`` limit applies independently to each
        yielded batch.
        """

        shape = {"y": 256, "x": 256} if batch_shape is None else batch_shape
        if set(shape) != {"y", "x"}:
            raise ValueError("batch_shape must contain exactly 'y' and 'x'")
        try:
            batch_rows = shape["y"]
            batch_cols = shape["x"]
        except (KeyError, TypeError):
            raise ValueError("batch_shape must contain integer 'y' and 'x' values") from None
        if (
            isinstance(batch_rows, bool)
            or isinstance(batch_cols, bool)
            or not isinstance(batch_rows, int)
            or not isinstance(batch_cols, int)
            or batch_rows <= 0
            or batch_cols <= 0
        ):
            raise ValueError("batch_shape must contain positive integer 'y' and 'x' values")

        grid_bounds = self.grid.transform_bounds(bounds, crs)
        row0, row1, col0, col1 = self.grid.window_for_bounds(grid_bounds)

        # Normalize iterables once; a generator must be reusable for every
        # spatial batch.
        selected_years: int | tuple[int, ...] | None
        if years is None or isinstance(years, int):
            selected_years = years
        else:
            selected_years = tuple(years)
        selected_variables = tuple(variables) if variables is not None else None
        self._year_positions(selected_years)
        self._validate_variables(selected_variables)

        for batch_row0 in range(row0, row1, batch_rows):
            batch_row1 = min(batch_row0 + batch_rows, row1)
            for batch_col0 in range(col0, col1, batch_cols):
                batch_col1 = min(batch_col0 + batch_cols, col1)
                yield self._query_window(
                    row0=batch_row0,
                    row1=batch_row1,
                    col0=batch_col0,
                    col1=batch_col1,
                    years=selected_years,
                    variables=selected_variables,
                )

    def export_bbox(
        self,
        bounds: tuple[float, float, float, float],
        output: str | Path,
        *,
        format: str = "zarr",
        years: int | Iterable[int] | None = None,
        variables: Sequence[str] | None = None,
        crs: str | CRS = "EPSG:4326",
        batch_shape: Mapping[str, int] | None = None,
        overwrite: bool = False,
    ) -> list[Path]:
        """Write a bounding box to NetCDF, Zarr, or multiband COG files.

        With ``batch_shape=None`` the complete query is materialized once:
        NetCDF and Zarr write one output, while COG writes one multiband
        raster per year. With ``batch_shape`` set, outputs are spatially
        sharded and written one batch at a time. COG bands are the selected
        variables and are stored as float32 so mixed source dtypes can share
        one raster. Returning paths rather than datasets keeps batch export
        bounded by the configured batch size.

        Zarr support requires the optional ``zarr`` package. COG output uses
        Rasterio/GDAL and is written in the grid CRS with the batch affine
        transform.
        """

        output_path = Path(output)
        output_path.mkdir(parents=True, exist_ok=True)
        output_format = format.lower().lstrip(".")
        aliases = {
            "nc": "netcdf",
            "ncdf": "netcdf",
            "netcdf4": "netcdf",
            "tif": "cog",
            "tiff": "cog",
            "geotiff": "cog",
        }
        output_format = aliases.get(output_format, output_format)
        if output_format not in {"netcdf", "zarr", "cog"}:
            raise ValueError("format must be one of: 'netcdf', 'zarr', or 'cog'")

        written: list[Path] = []
        batch_mode = batch_shape is not None
        if batch_mode:
            datasets = self.iter_bbox(
                bounds,
                years=years,
                variables=variables,
                crs=crs,
                batch_shape=batch_shape,
            )
        else:
            datasets = iter(
                (
                    self.query_bbox(
                        bounds,
                        years=years,
                        variables=variables,
                        crs=crs,
                    ),
                )
            )

        for batch_index, dataset in enumerate(datasets):
            if output_format == "netcdf":
                if not any(
                    importlib.util.find_spec(module) is not None
                    for module in ("netCDF4", "h5netcdf", "scipy")
                ):
                    raise ModuleNotFoundError(
                        "NetCDF export requires a backend; install it with "
                        "'pip install dhidb[netcdf]'."
                    )
                filename = f"batch_{batch_index:06d}.nc" if batch_mode else "data.nc"
                path = output_path / filename
                if path.exists() and not overwrite:
                    raise FileExistsError(path)
                dataset.to_netcdf(path)
                written.append(path)
                continue

            if output_format == "zarr":
                filename = f"batch_{batch_index:06d}.zarr" if batch_mode else "data.zarr"
                path = output_path / filename
                if path.exists() and not overwrite:
                    raise FileExistsError(path)
                try:
                    dataset.to_zarr(path, mode="w")
                except ModuleNotFoundError as exc:
                    raise ModuleNotFoundError(
                        "Zarr export requires the optional 'zarr' package; "
                        "install it with 'pip install zarr'."
                    ) from exc
                written.append(path)
                continue

            try:
                import rasterio
                from affine import Affine
            except ImportError as exc:  # pragma: no cover - dependency is required
                raise ImportError("COG export requires rasterio and affine") from exc

            transform = Affine(*dataset.attrs["transform"])
            crs_wkt = dataset.attrs["crs_wkt"]
            for time_index, year in enumerate(dataset.time.values.tolist()):
                filename = (
                    f"batch_{batch_index:06d}_{int(year)}.tif"
                    if batch_mode
                    else f"{int(year)}.tif"
                )
                path = output_path / filename
                if path.exists() and not overwrite:
                    raise FileExistsError(path)
                values = [
                    np.asarray(dataset[name].values[time_index], dtype="float32")
                    for name in dataset.data_vars
                ]
                with rasterio.open(
                    path,
                    "w",
                    driver="COG",
                    width=values[0].shape[1],
                    height=values[0].shape[0],
                    count=len(values),
                    dtype="float32",
                    crs=crs_wkt,
                    transform=transform,
                    nodata=np.nan,
                    compress="DEFLATE",
                    blocksize=256,
                    BIGTIFF="IF_SAFER",
                ) as destination:
                    for band_index, (name, array) in enumerate(
                        zip(dataset.data_vars, values, strict=True), start=1
                    ):
                        destination.write(array, band_index)
                        destination.set_band_description(band_index, name)
                written.append(path)

        return written

    def query_point(
        self,
        longitude: float,
        latitude: float,
        *,
        years: int | Iterable[int] | None = None,
        variables: Sequence[str] | None = None,
        crs: str | CRS = "EPSG:4326",
    ) -> pd.DataFrame:
        """Return the grid cell containing a point as a tidy dataframe."""

        transformer = Transformer.from_crs(crs, self.grid.crs, always_xy=True)
        grid_x, grid_y = transformer.transform(longitude, latitude)
        col, row = (~self.grid.affine) * (grid_x, grid_y)
        row_index, col_index = int(np.floor(row)), int(np.floor(col))
        if not (0 <= row_index < self.grid.height and 0 <= col_index < self.grid.width):
            raise ValueError("The requested point lies outside the DHIDB grid.")
        dataset = self._query_window(
            row0=row_index,
            row1=row_index + 1,
            col0=col_index,
            col1=col_index + 1,
            years=years,
            variables=variables,
        )
        frame = dataset.to_dataframe().reset_index()
        return frame.drop(columns=["x", "y"]).set_index("time")

    def query_polygon(
        self,
        geometry: Any,
        *,
        years: int | Iterable[int] | None = None,
        variables: Sequence[str] | None = None,
        crs: str | CRS = "EPSG:4326",
        all_touched: bool = False,
    ) -> xr.Dataset:
        """Return an AOI bounding box with pixels outside the polygon masked."""

        geom = _load_geometry(geometry)
        transformer = Transformer.from_crs(crs, self.grid.crs, always_xy=True)
        grid_geom = transform_geometry(transformer.transform, geom)
        row0, row1, col0, col1 = self.grid.window_for_bounds(grid_geom.bounds)
        dataset = self._query_window(
            row0=row0,
            row1=row1,
            col0=col0,
            col1=col1,
            years=years,
            variables=variables,
        )
        mask = geometry_mask(
            [grid_geom.__geo_interface__],
            out_shape=(row1 - row0, col1 - col0),
            transform=self.grid.subset_transform(row0, col0),
            invert=True,
            all_touched=all_touched,
        )
        return dataset.where(xr.DataArray(mask, dims=("y", "x")))

    def close(self) -> None:
        """Close the persistent TileDB read handle."""

        if self._array is not None:
            if self._array.isopen:
                self._array.close()
            self._array = None

    def __enter__(self) -> DHIProvider:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def _load_geometry(value: Any):
    if isinstance(value, (str, Path)):
        raw = json.loads(Path(value).read_text(encoding="utf-8"))
    elif hasattr(value, "__geo_interface__"):
        raw = value.__geo_interface__
    elif isinstance(value, dict):
        raw = value
    else:
        raise TypeError("geometry must be a shapely object, GeoJSON mapping, or GeoJSON path")

    kind = raw.get("type")
    if kind == "FeatureCollection":
        geometries = [shape(feature["geometry"]) for feature in raw.get("features", [])]
        return unary_union(geometries) if geometries else GeometryCollection()
    if kind == "Feature":
        return shape(raw["geometry"])
    return shape(raw)
