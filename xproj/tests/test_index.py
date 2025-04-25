import pyproj
import pytest
import xarray as xr
from xarray.indexes import PandasIndex

from xproj import CRSIndex


def test_crsindex_init() -> None:
    index = CRSIndex(pyproj.CRS.from_user_input("epsg:4326"))
    assert index.crs == pyproj.CRS.from_user_input("epsg:4326")


def test_create_crsindex() -> None:
    ds = xr.Dataset(coords={"spatial_ref": 0})
    crs = pyproj.CRS.from_user_input("epsg:4326")
    attrs = crs.to_cf()

    # no attribute
    ds.coords["spatial_ref"] = (tuple(), 0, {})
    with pytest.raises(ValueError, match="CRS could not be constructed from attrs"):
        indexed = ds.set_xindex("spatial_ref", CRSIndex)

    # pass CRS as build option
    indexed = ds.set_xindex("spatial_ref", CRSIndex, crs=crs)
    assert "spatial_ref" in indexed.xindexes
    assert isinstance(indexed.xindexes["spatial_ref"], CRSIndex)
    assert getattr(indexed.xindexes["spatial_ref"], "crs") == crs

    # pass CRS as CF attributes
    ds.coords["spatial_ref"] = (tuple(), 0, attrs)
    indexed = ds.set_xindex("spatial_ref", CRSIndex)
    assert "spatial_ref" in indexed.xindexes
    assert isinstance(indexed.xindexes["spatial_ref"], CRSIndex)
    assert getattr(indexed.xindexes["spatial_ref"], "crs") == crs

    # pass CRS as "spatial_ref" attribute (WKT) for GDAL compat
    ds.coords["spatial_ref"] = (tuple(), 0, {"spatial_ref": attrs["crs_wkt"]})
    indexed = ds.set_xindex("spatial_ref", CRSIndex)
    assert "spatial_ref" in indexed.xindexes
    assert isinstance(indexed.xindexes["spatial_ref"], CRSIndex)
    assert getattr(indexed.xindexes["spatial_ref"], "crs") == crs


def test_create_crsindex_error() -> None:
    ds = xr.Dataset(coords={"spatial_ref": 0, "spatial_ref2": ("x", [0])})

    with pytest.raises(ValueError, match="from one scalar variable"):
        ds.set_xindex(["spatial_ref", "spatial_ref2"], CRSIndex)

    with pytest.raises(ValueError, match="from one scalar variable"):
        ds.set_xindex("spatial_ref2", CRSIndex)


def test_crsindex_repr() -> None:
    crs = pyproj.CRS.from_user_input("epsg:4326")
    index = CRSIndex(crs)

    expected = f"CRSIndex\n{crs!r}"
    assert repr(index) == expected


def test_crsindex_repr_inline() -> None:
    crs = pyproj.CRS.from_user_input("epsg:4326")
    index = CRSIndex(crs)

    expected = "CRSIndex (crs=EPSG:4326)"
    assert index._repr_inline_(100) == expected

    expected_trunc = "CRSIndex (crs=EPSG: ...)"
    assert index._repr_inline_(5) == expected_trunc


def test_crsindex_equals() -> None:
    idx1 = CRSIndex(pyproj.CRS.from_user_input("epsg:4326"))
    idx2 = CRSIndex(pyproj.CRS.from_user_input("epsg:4326"))
    assert idx1.equals(idx2) is True

    idx3 = PandasIndex([0, 1], "x")
    assert idx1.equals(idx3) is False  # type: ignore

    idx4 = CRSIndex(pyproj.CRS.from_user_input("epsg:4978"))
    assert idx1.equals(idx4) is False
