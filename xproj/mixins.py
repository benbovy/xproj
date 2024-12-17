import abc
from collections.abc import Hashable
from typing import TypeVar

import pyproj
import xarray as xr

T_Xarray_Object = TypeVar("T_Xarray_Object", xr.Dataset, xr.DataArray)


class ProjAccessorMixin(abc.ABC):
    """Mixin class that marks xproj support for an Xarray accessor."""

    @abc.abstractmethod
    def _proj_set_crs(self, crs_coord_name: Hashable, crs: pyproj.CRS) -> T_Xarray_Object:
        """Method called when setting a new CRS via ``.proj.assign_crs()``.

        Parameters
        ----------
        crs_coord_name : Hashable
            The name of the spatial reference (scalar) coordinate
            to which the CRS has been set.
        crs : pyproj.CRS
            The new CRS attached to the spatial reference coordinate.

        Returns
        -------
        xarray.Dataset or xarray.DataArray
            Either a new or an existing Dataset or DataArray.

        """
        ...


class ProjIndexMixin(abc.ABC):
    """Mixin class that marks xproj support for an Xarray index."""

    @abc.abstractmethod
    def _proj_get_crs(self) -> pyproj.CRS:
        """XProj access to the CRS of the index.

        Returns
        -------
        pyproj.CRS
            The CRS of the index.

        """
        ...

    def _proj_set_crs(self, crs_coord_name: Hashable, crs: pyproj.CRS) -> T_Xarray_Object | None:
        """Method called when mapping a CRS to index coordinate(s) via
        ``.proj.map_crs()``.

        Parameters
        ----------
        crs_coord_name : Hashable
            The name of the spatial reference (scalar) coordinate.
        crs : pyproj.CRS
            The new CRS attached to the spatial reference coordinate.

        Returns
        -------
        xarray.Dataset or xarray.DataArray or None
            Either a new or an existing Dataset or DataArray,
            or None (default).

        """
        return None
