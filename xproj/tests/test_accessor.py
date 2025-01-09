import pyproj
import pytest
import xarray as xr
from xarray.indexes import Index, PandasIndex

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


class ImmutableCRSIndex(PandasIndex):
    def _proj_get_crs(self):
        return pyproj.CRS.from_epsg(4326)


class MutableCRSIndex(PandasIndex):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._crs = None

    def _proj_get_crs(self):
        return self._crs

    def _proj_set_crs(self, crs_coord_name, crs):
        self._crs = crs
        return self

    def _copy(self, deep=True, memo=None):
        # bug in PandasIndex? crs attribute not copied here
        obj = super()._copy(deep=deep, memo=memo)
        obj._crs = self._crs
        return obj


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
    ds = xr.Dataset(coords={"foo": ("x", [1, 2])}).set_xindex("foo", ImmutableCRSIndex)

    assert ds.proj.crs_aware_indexes["foo"] is ds.xindexes["foo"]

    # should also test the cached value
    assert list(ds.proj.crs_aware_indexes) == ["foo"]

    # frozen dict
    with pytest.raises(TypeError, match="not support item assignment"):
        ds.proj.crs_aware_indexes["new"] = ImmutableCRSIndex([2, 3], "x")

    with pytest.raises(TypeError, match="not support item deletion"):
        del ds.proj.crs_aware_indexes["foo"]


def test_accessor_callable(spatial_xr_obj) -> None:
    actual = spatial_xr_obj.proj("spatial_ref").crs
    expected = spatial_xr_obj.xindexes["spatial_ref"].crs
    assert actual == expected

    # 2nd spatial reference coordinate
    obj2 = spatial_xr_obj.assign_coords(spatial_ref2=0)
    obj2 = obj2.set_xindex("spatial_ref2", xproj.CRSIndex, crs=pyproj.CRS.from_epsg(4978))
    assert obj2.proj("spatial_ref2").crs == obj2.xindexes["spatial_ref2"].crs


def test_accessor_callable_crs_aware_index() -> None:
    ds = xr.Dataset(coords={"foo": ("x", [1, 2])}).set_xindex("foo", ImmutableCRSIndex)

    assert ds.proj("foo").crs == ds.xindexes["foo"]._proj_get_crs()  # type: ignore


def test_accessor_callable_error(spatial_xr_obj) -> None:
    class DummyIndex(xr.Index):
        @classmethod
        def from_variables(cls, variables, *, options):
            return cls()

    obj = spatial_xr_obj.assign_coords(x=[1, 2], foo=("x", [3, 4]), a=0, b=0)
    obj = obj.set_xindex("b", DummyIndex)

    with pytest.raises(KeyError, match="no coordinate 'bar' found"):
        obj.proj("bar")

    with pytest.raises(ValueError, match="coordinate 'foo' is not a scalar coordinate"):
        obj.proj("foo")

    with pytest.raises(ValueError, match="coordinate 'a' has no index"):
        obj.proj("a")

    with pytest.raises(ValueError, match="coordinate 'b' index is not a CRSIndex"):
        obj.proj("b")


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

    ds = ds.drop_indexes("foo").set_xindex("foo", ImmutableCRSIndex)
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

    # multiple spatial reference coordinates
    ds2 = ds.proj.assign_crs(a=pyproj.CRS.from_epsg(4326), b=pyproj.CRS.from_epsg(4978))
    assert "a" in ds2.proj.crs_indexes
    assert "b" in ds2.proj.crs_indexes


def test_accessor_map_crs(spatial_xr_obj) -> None:
    # nothing happens but should return a copy
    assert spatial_xr_obj.proj.map_crs() is not spatial_xr_obj

    obj = spatial_xr_obj.assign_coords(foo=("x", [1, 2])).set_xindex("foo", MutableCRSIndex)
    actual = obj.proj.map_crs(spatial_ref=["foo"])
    actual2 = obj.proj.map_crs({"spatial_ref": ["foo"]})
    assert actual.proj("spatial_ref").crs == actual.proj("foo").crs
    assert actual2.proj("spatial_ref").crs == actual2.proj("foo").crs

    # not a crs-aware index
    obj = spatial_xr_obj.assign_coords(x=[1, 2])
    with pytest.warns(UserWarning, match="won't have any effect"):
        obj.proj.map_crs(spatial_ref=["x"])

    with pytest.raises(KeyError, match="no coordinate 'x' found"):
        spatial_xr_obj.proj.map_crs(spatial_ref=["x"])

    obj = spatial_xr_obj.assign_coords(foo=("x", [1, 2]))
    with pytest.raises(KeyError, match="no index found"):
        obj.proj.map_crs(spatial_ref=["foo"])

    obj = spatial_xr_obj.assign_coords(foo=("x", [1, 2])).set_xindex("foo", MutableCRSIndex)
    with pytest.raises(KeyError, match="no coordinate 'a' found"):
        obj.proj.map_crs(a=["foo"])


def test_accessor_map_crs_multicoord_index() -> None:
    class RasterIndex(Index):
        def __init__(self, xy_indexes):
            self._xyindexes = xy_indexes
            self._crs = None

        @classmethod
        def from_variables(cls, variables, *, options):
            xy_indexes = {
                "x": PandasIndex.from_variables({"x": variables["x"]}, options={}),
                "y": PandasIndex.from_variables({"y": variables["y"]}, options={}),
            }
            return cls(xy_indexes)

        def _proj_get_crs(self):
            return self._crs

        def _proj_set_crs(self, spatial_ref, crs):
            self._crs = crs
            return self

    coords = xr.Coordinates({"x": [1, 2], "y": [3, 4]}, indexes={})
    ds = xr.Dataset(coords=coords).set_xindex(["x", "y"], RasterIndex)
    ds = ds.proj.assign_crs(spatial_ref=pyproj.CRS.from_epsg(4326))

    actual = ds.proj.map_crs(spatial_ref=["x", "y"])
    for name in ("x", "y"):
        assert actual.proj(name).crs == pyproj.CRS.from_epsg(4326)

    with pytest.raises(ValueError, match="missing indexed coordinate"):
        ds.proj.map_crs(spatial_ref=["x"])


def test_accessor_write_crs_info(spatial_xr_obj) -> None:
    obj_with_attrs = spatial_xr_obj.proj.write_crs_info()
    assert "crs_wkt" in obj_with_attrs.spatial_ref.attrs

    # test attrs unchanged in original object
    assert "crs_wkt" not in spatial_xr_obj.spatial_ref.attrs

    # test spatial ref coordinate provided explicitly
    obj_with_attrs2 = spatial_xr_obj.proj.write_crs_info("spatial_ref")
    assert "crs_wkt" in obj_with_attrs2.spatial_ref.attrs

    # test alternative func
    obj_with_attrs3 = spatial_xr_obj.proj.write_crs_info(func=xproj.format_full_cf_gdal)
    assert "crs_wkt" in obj_with_attrs3.spatial_ref.attrs
    assert "spatial_ref" in obj_with_attrs3.spatial_ref.attrs
    assert "grid_mapping_name" in obj_with_attrs3.spatial_ref.attrs
