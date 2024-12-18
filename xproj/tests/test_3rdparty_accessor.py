import pyproj
import pytest
import xarray as xr

import xproj
from xproj.accessor import GeoAccessorRegistry


@xproj.register_accessor
@xr.register_dataset_accessor("test_3rdparty")
@xr.register_dataarray_accessor("test_3rdparty")
class Test3rdPartyAccessor(xproj.ProjAccessorMixin):
    __test__ = False

    def __init__(self, obj):
        self._obj = obj
        self._crs = None
        self._crs_coord_name = None

    @property
    def crs(self):
        return self._crs

    @property
    def crs_coord_name(self):
        return self._crs_coord_name

    def _proj_set_crs(self, crs_coord_name, crs):
        self._crs = crs
        self._crs_coord_name = crs_coord_name
        return self._obj


def test_accessor_mixin_abstract() -> None:
    class Accessor(xproj.ProjAccessorMixin):
        def __init__(self, obj):
            self._obj = obj

    with pytest.raises(TypeError):
        Accessor(xr.Dataset())  # type: ignore


def test_register_accessor() -> None:
    ds = xr.Dataset()
    assert GeoAccessorRegistry.get_accessors(ds)[0] is ds.test_3rdparty

    da = xr.DataArray()
    assert GeoAccessorRegistry.get_accessors(da)[0] is da.test_3rdparty

    class NotAnAccessor: ...

    with pytest.raises(ValueError, match=r"not an.*accessor decorated class"):
        xproj.register_accessor(NotAnAccessor)


def test_assign_crs() -> None:
    ds = xr.Dataset().proj.assign_crs(spatial_ref=pyproj.CRS.from_epsg(4326))

    assert ds.test_3rdparty.crs == pyproj.CRS.from_epsg(4326)
    assert ds.test_3rdparty.crs_coord_name == "spatial_ref"
