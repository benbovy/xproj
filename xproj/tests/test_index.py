import pyproj
import pytest
import xarray as xr
from xarray.indexes import PandasIndex

from xproj import CRSIndex


def test_crsindex_init():
    index = CRSIndex(pyproj.CRS.from_user_input("epsg:4326"))
    assert index.crs == pyproj.CRS.from_user_input("epsg:4326")


def test_create_crsindex():
    ds = xr.Dataset(coords={"spatial_ref": 0})

    # pass CRS via build option
    crs = pyproj.CRS.from_user_input("epsg:4326")
    ds_index = ds.set_xindex("spatial_ref", CRSIndex, crs=crs)
    assert "spatial_ref" in ds_index.xindexes
    assert isinstance(ds_index.xindexes["spatial_ref"], CRSIndex)
    assert getattr(ds_index.xindexes["spatial_ref"], "crs") == crs


def test_create_crsindex_error():
    ds = xr.Dataset(coords={"spatial_ref": 0, "spatial_ref2": ("x", [0])})

    with pytest.raises(ValueError, match="from one scalar variable"):
        ds.set_xindex(["spatial_ref", "spatial_ref2"], CRSIndex)

    with pytest.raises(ValueError, match="from one scalar variable"):
        ds.set_xindex("spatial_ref2", CRSIndex)


def test_crsindex_repr():
    crs = pyproj.CRS.from_user_input("epsg:4326")
    index = CRSIndex(crs)

    expected = f"CRSIndex\n{crs!r}"
    assert repr(index) == expected


def test_crsindex_repr_inline():
    crs = pyproj.CRS.from_user_input("epsg:4326")
    index = CRSIndex(crs)

    expected = "CRSIndex (crs=EPSG:4326)"
    assert index._repr_inline_(100) == expected

    expected_trunc = "CRSIndex (crs=EPSG: ...)"
    assert index._repr_inline_(5) == expected_trunc


def test_crsindex_equals():
    idx1 = CRSIndex(pyproj.CRS.from_user_input("epsg:4326"))
    idx2 = CRSIndex(pyproj.CRS.from_user_input("epsg:4326"))
    assert idx1.equals(idx2) is True

    idx3 = PandasIndex([0, 1], "x")
    assert idx1.equals(idx3) is False  # type: ignore

    idx4 = CRSIndex(pyproj.CRS.from_user_input("epsg:4978"))
    assert idx1.equals(idx4) is False
