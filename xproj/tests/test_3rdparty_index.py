import pyproj
import pytest
import xarray as xr
from xarray.indexes import PandasIndex

import xproj


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


def test_index_mixin_abstract() -> None:
    class Index(PandasIndex, xproj.ProjAccessorMixin):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

    with pytest.raises(TypeError):
        Index([1, 2], "x")  # type: ignore


def test_map_crs() -> None:
    ds = (
        xr.Dataset(coords={"foo": ("x", [1, 2]), "bar": ("y", [3, 4])})
        .set_xindex("foo", ImmutableCRSIndex)
        .set_xindex("bar", MutableCRSIndex)
        .proj.assign_crs(spatial_ref=pyproj.CRS.from_epsg(4978))
    )

    with pytest.warns(UserWarning, match="won't have any effect"):
        ds_mapped = ds.proj.map_crs(spatial_ref=["foo"])
    ds_mapped = ds_mapped.proj.map_crs(spatial_ref=["bar"])

    assert ds_mapped.proj("foo").crs == pyproj.CRS.from_epsg(4326)
    assert ds_mapped.proj("bar").crs == pyproj.CRS.from_epsg(4978)
