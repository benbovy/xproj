import abc
from collections.abc import Hashable
from typing import TypeVar

import pyproj
import xarray as xr

T_Xarray_Object = TypeVar("T_Xarray_Object", xr.Dataset, xr.DataArray)


class ProjAccessorMixin(abc.ABC):
    """Mixin class that marks xproj support for an Xarray accessor."""

    @abc.abstractmethod
    def _proj_set_crs(self, crs_coord_name: Hashable, crs: pyproj.CRS) -> T_Xarray_Object: ...


class ProjIndexMixin(abc.ABC):
    """Mixin class that marks xproj support for an Xarray index."""

    @abc.abstractmethod
    def _proj_get_crs(self) -> pyproj.CRS: ...

    def _proj_set_crs(self, crs_coord_name: Hashable, crs: pyproj.CRS) -> T_Xarray_Object | None:
        return None
