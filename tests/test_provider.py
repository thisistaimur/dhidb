import numpy as np
import pytest
from shapely.geometry import box

from dhidb import DHIProvider


def test_properties_and_bbox_query(sample_array):
    with DHIProvider(array_uri=sample_array) as provider:
        assert provider.years == (2020, 2021)
        assert set(provider.variables) == {"dhi_cum", "dhi_min", "dhi_var", "valid_count"}

        result = provider.query_bbox(
            (-179.9, 87.1, -176.1, 89.9),
            years=[2020, 2021],
            variables=["dhi_cum", "dhi_min"],
        )

    assert result.sizes == {"time": 2, "y": 3, "x": 4}
    assert result.dhi_min.attrs["units"] == "m2 m-2"
    np.testing.assert_allclose(result.dhi_cum.values.ravel(), np.arange(24))


def test_point_query(sample_array):
    with DHIProvider(array_uri=sample_array) as provider:
        result = provider.query_point(-179.5, 89.5, years=[2020, 2021])

    assert result.index.tolist() == [2020, 2021]
    assert result["dhi_cum"].tolist() == [0.0, 12.0]
    assert result["valid_count"].tolist() == [36, 36]


def test_polygon_masks_outside_cells(sample_array):
    with DHIProvider(array_uri=sample_array) as provider:
        result = provider.query_polygon(
            box(-180, 88, -178, 90),
            years=2020,
            variables=["dhi_cum"],
        )

    assert result.sizes == {"time": 1, "y": 2, "x": 2}
    assert int(np.isfinite(result.dhi_cum.values).sum()) == 4


def test_query_size_guard(sample_array):
    with DHIProvider(array_uri=sample_array, max_cells=2) as provider:
        with pytest.raises(ValueError, match="safety limit"):
            provider.query_bbox((-180, 87, -176, 90), years=2020)


def test_iter_bbox_yields_bounded_batches(sample_array):
    with DHIProvider(array_uri=sample_array) as provider:
        batches = list(
            provider.iter_bbox(
                (-179.9, 87.1, -176.1, 89.9),
                years=(year for year in [2020, 2021]),
                variables=["dhi_cum"],
                batch_shape={"y": 2, "x": 2},
            )
        )

    assert len(batches) == 4
    assert [(batch.sizes["y"], batch.sizes["x"]) for batch in batches] == [
        (2, 2),
        (2, 2),
        (1, 2),
        (1, 2),
    ]
    np.testing.assert_allclose(
        np.sort(np.concatenate([batch.dhi_cum.values.ravel() for batch in batches])),
        np.arange(24),
    )


def test_iter_bbox_validates_batch_shape(sample_array):
    with DHIProvider(array_uri=sample_array) as provider:
        with pytest.raises(ValueError, match="exactly 'y' and 'x'"):
            list(provider.iter_bbox((-180, 87, -176, 90), batch_shape={"y": 2}))

        with pytest.raises(ValueError, match="positive integer"):
            list(
                provider.iter_bbox(
                    (-180, 87, -176, 90),
                    batch_shape={"y": 0, "x": 2},
                )
            )


def test_export_bbox_netcdf_writes_batch_files(sample_array, tmp_path):
    with DHIProvider(array_uri=sample_array) as provider:
        paths = provider.export_bbox(
            (-179.9, 87.1, -176.1, 89.9),
            tmp_path / "netcdf",
            format="netcdf",
            years=2020,
            variables=["dhi_cum"],
            batch_shape={"y": 2, "x": 2},
        )

    assert len(paths) == 4
    assert all(path.suffix == ".nc" for path in paths)


def test_export_bbox_cog_writes_multiband_batch_files(sample_array, tmp_path):
    with DHIProvider(array_uri=sample_array) as provider:
        paths = provider.export_bbox(
            (-179.9, 87.1, -176.1, 89.9),
            tmp_path / "cog",
            format="cog",
            years=2020,
            variables=["dhi_cum", "valid_count"],
            batch_shape={"y": 2, "x": 2},
        )

    assert len(paths) == 4
    assert all(path.suffix == ".tif" for path in paths)


def test_export_bbox_nonbatch_writes_one_output_per_format(sample_array, tmp_path):
    with DHIProvider(array_uri=sample_array) as provider:
        netcdf_paths = provider.export_bbox(
            (-179.9, 87.1, -176.1, 89.9),
            tmp_path / "netcdf",
            format="netcdf",
            years=[2020, 2021],
            variables=["dhi_cum"],
        )
        cog_paths = provider.export_bbox(
            (-179.9, 87.1, -176.1, 89.9),
            tmp_path / "cog",
            format="cog",
            years=[2020, 2021],
            variables=["dhi_cum", "valid_count"],
        )

    assert netcdf_paths == [tmp_path / "netcdf" / "data.nc"]
    assert cog_paths == [tmp_path / "cog" / "2020.tif", tmp_path / "cog" / "2021.tif"]


def test_unknown_year_and_variable(sample_array):
    with DHIProvider(array_uri=sample_array) as provider:
        with pytest.raises(ValueError, match="Years not available"):
            provider.query_point(-179.5, 89.5, years=1999)
        with pytest.raises(ValueError, match="Unknown variables"):
            provider.query_point(-179.5, 89.5, variables=["missing"])
