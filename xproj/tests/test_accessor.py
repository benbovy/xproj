import pyproj
import pytest
import xarray as xr
from xarray.indexes import PandasIndex

import xproj


@pytest.fixture
def spatial_dataset() -> xr.Dataset:
    crs = pyproj.CRS.from_user_input("epsg:4326")
    ds = xr.Dataset(coords={"spatial_ref": 0})
    return ds.set_xindex("spatial_ref", xproj.CRSIndex, crs=crs)


@pytest.fixture
def spatial_dataarray() -> xr.DataArray:
    crs = pyproj.CRS.from_user_input("epsg:4326")
    da = xr.DataArray([1, 2], coords={"spatial_ref": 0}, dims="x")
    return da.set_xindex("spatial_ref", xproj.CRSIndex, crs=crs)


@pytest.fixture(params=["Dataset", "DataArray"])
def spatial_xr_obj(request, spatial_dataset, spatial_dataarray):
    if request.param == "Dataset":
        yield spatial_dataset
    else:
        yield spatial_dataarray


class GeoIndex(PandasIndex):
    def _proj_get_crs(self):
        return pyproj.CRS.from_epsg(4326)


def test_accessor_crs_indexes(spatial_xr_obj) -> None:
    actual = spatial_xr_obj.proj.crs_indexes["spatial_ref"]
    expected = spatial_xr_obj.xindexes["spatial_ref"]
    assert actual is expected

    # should also test the cached value
    assert list(spatial_xr_obj.proj.crs_indexes) == ["spatial_ref"]

    # frozen dict
    with pytest.raises(TypeError, match="not support item assignment"):
        spatial_xr_obj.proj.crs_indexes["new"] = xproj.CRSIndex(pyproj.CRS.from_epsg(4326))

    with pytest.raises(TypeError, match="not support item deletion"):
        del spatial_xr_obj.proj.crs_indexes["new"]


def test_accessor_crs_aware_indexes() -> None:
    ds = xr.Dataset(coords={"foo": ("x", [1, 2])}).set_xindex("foo", GeoIndex)

    assert ds.proj.crs_aware_indexes["foo"] is ds.xindexes["foo"]

    # should also test the cached value
    assert list(ds.proj.crs_aware_indexes) == ["foo"]

    # frozen dict
    with pytest.raises(TypeError, match="not support item assignment"):
        ds.proj.crs_aware_indexes["new"] = GeoIndex([2, 3], "x")

    with pytest.raises(TypeError, match="not support item deletion"):
        del ds.proj.crs_aware_indexes["foo"]


def test_accessor_callable(spatial_xr_obj) -> None:
    actual = spatial_xr_obj.proj("spatial_ref").crs
    expected = spatial_xr_obj.xindexes["spatial_ref"].crs
    assert actual == expected


def test_accessor_callable_crs_aware_index() -> None:
    ds = xr.Dataset(coords={"foo": ("x", [1, 2])}).set_xindex("foo", GeoIndex)

    assert ds.proj("foo").crs == ds.xindexes["foo"]._proj_get_crs()  # type: ignore


def test_accessor_callable_error(spatial_xr_obj) -> None:
    obj = spatial_xr_obj.assign_coords(x=[1, 2], foo=("x", [3, 4]))

    with pytest.raises(KeyError, match="no coordinate 'bar' found"):
        obj.proj("bar")

    with pytest.raises(ValueError, match="coordinate 'foo' has no index"):
        obj.proj("foo")

    with pytest.raises(ValueError, match="coordinate 'x' index is not a CRSIndex"):
        obj.proj("x")

    obj = obj.assign_coords(spatial_ref2=0)
    obj = obj.set_xindex("spatial_ref2", xproj.CRSIndex, crs=pyproj.CRS.from_epsg(4978))

    with pytest.raises(ValueError, match="found multiple coordinates with a CRSIndex"):
        obj.proj("spatial_ref2")


def test_accessor_assert_one_index() -> None:
    ds = xr.Dataset()

    with pytest.raises(AssertionError, match="no CRS found"):
        ds.proj.assert_one_crs_index()

    ds = ds.assign_coords({"a": 0, "b": 1})
    ds = ds.set_xindex("a", xproj.CRSIndex, crs=pyproj.CRS.from_epsg(4326))
    ds = ds.set_xindex("b", xproj.CRSIndex, crs=pyproj.CRS.from_epsg(4978))

    with pytest.raises(AssertionError, match="multiple CRS found"):
        ds.proj.assert_one_crs_index()


def test_accessor_crs() -> None:
    class NoCRSIndex(PandasIndex):
        def _proj_get_crs(self):
            return None

    ds = xr.Dataset()
    assert ds.proj.crs is None
    assert ds.proj.crs is None  # test cached value

    ds = ds.assign_coords(foo=("x", [1, 2])).set_xindex("foo", NoCRSIndex)
    assert ds.proj.crs is None

    ds = ds.drop_indexes("foo").set_xindex("foo", GeoIndex)
    assert ds.proj.crs == pyproj.CRS.from_epsg(4326)

    ds = ds.drop_vars("foo")
    ds = ds.assign_coords(spatial_ref=0)
    ds = ds.set_xindex("spatial_ref", xproj.CRSIndex, crs=pyproj.CRS.from_epsg(4326))
    assert ds.proj.crs == pyproj.CRS.from_epsg(4326)

    ds = ds.assign_coords(spatial_ref2=0)
    ds = ds.set_xindex("spatial_ref2", xproj.CRSIndex, crs=pyproj.CRS.from_epsg(4978))
    with pytest.raises(ValueError, match="found multiple CRS"):
        ds.proj.crs


def test_accessor_assign_crs() -> None:
    ds = xr.Dataset()

    # nothing happens but should return a copy
    assert ds.proj.assign_crs() is not ds

    actual = ds.proj.assign_crs(spatial_ref=pyproj.CRS.from_epsg(4326))
    actual2 = ds.proj.assign_crs({"spatial_ref": pyproj.CRS.from_epsg(4326)})
    expected = ds.assign_coords(spatial_ref=0).set_xindex(
        "spatial_ref", xproj.CRSIndex, crs=pyproj.CRS.from_epsg(4326)
    )
    xr.testing.assert_identical(actual, expected)
    xr.testing.assert_identical(actual2, expected)

    with pytest.raises(ValueError, match="coordinate 'spatial_ref' already has an index"):
        actual.proj.assign_crs(spatial_ref=pyproj.CRS.from_epsg(4978))

    actual = actual.proj.assign_crs(spatial_ref=pyproj.CRS.from_epsg(4978), allow_override=True)
    expected = ds.assign_coords(spatial_ref=0).set_xindex(
        "spatial_ref", xproj.CRSIndex, crs=pyproj.CRS.from_epsg(4978)
    )
    xr.testing.assert_identical(actual, expected)

    with pytest.raises(ValueError, match="setting multiple CRS"):
        ds.proj.assign_crs(a=pyproj.CRS.from_epsg(4326), b=pyproj.CRS.from_epsg(4978))
