import abc
import sys
from collections.abc import Hashable
from typing import TYPE_CHECKING, Any, Generic, Self, TypeVar

import pyproj
import xarray as xr

try:
    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self
except ImportError:
    if TYPE_CHECKING:
        raise
    else:
        Self: Any = None

T_Xarray_Object = TypeVar("T_Xarray_Object", xr.Dataset, xr.DataArray)


class ProjAccessorMixin(abc.ABC, Generic[T_Xarray_Object]):
    """Mixin class that marks XProj support for an Xarray accessor."""

    @abc.abstractmethod
    def _proj_set_crs(self, spatial_ref: Hashable, crs: pyproj.CRS) -> T_Xarray_Object:
        """Method called when setting a new CRS via
        :py:meth:`xarray.Dataset.proj.assign_crs()`.

        Parameters
        ----------
        spatial_ref : Hashable
            The name of the spatial reference (scalar) coordinate
            to which the CRS has been set.
        crs : pyproj.crs.CRS
            The new CRS attached to the spatial reference coordinate.

        Returns
        -------
        xarray.Dataset or xarray.DataArray
            Either a new or an existing Dataset or DataArray.

        """
        ...


class ProjIndexMixin(abc.ABC):
    """Mixin class that marks XProj support for an Xarray index."""

    @abc.abstractmethod
    def _proj_get_crs(self) -> pyproj.CRS | None:
        """XProj access to the CRS of the index.

        Returns
        -------
        pyproj.crs.CRS or None
            The CRS of the index or None if not (yet) defined.

        """
        ...

    def _proj_set_crs(
        self: Self,
        spatial_ref: Hashable,
        crs: pyproj.CRS,
    ) -> Self:
        """Method called when mapping a CRS to index coordinate(s) via
        :py:meth:`xarray.Dataset.proj.map_crs`.

        Parameters
        ----------
        spatial_ref : Hashable
            The name of the spatial reference (scalar) coordinate.
        crs : pyproj.crs.CRS
            The new CRS attached to the spatial reference coordinate.

        Returns
        -------
        Index
            Either a new or an existing xarray Index.

        """
        raise NotImplementedError("This CRS-aware index does not support (re)setting the CRS.")

    def _proj_to_crs(
        self: Self,
        spatial_ref: Hashable,
        crs: pyproj.CRS,
    ) -> Self:
        """Method called when mapping a CRS to index coordinate(s) via
        :py:meth:`xarray.Dataset.proj.map_crs` with ``transform=True``.

        Parameters
        ----------
        spatial_ref : Hashable
            The name of the spatial reference (scalar) coordinate.
        crs : pyproj.crs.CRS
            The new CRS attached to the spatial reference coordinate.

        Returns
        -------
        Index
            Either a new or an existing xarray Index.

        """
        raise NotImplementedError(
            "This CRS-aware index does not support (re)setting the CRS "
            "with coordinate data transformation."
        )
