from __future__ import annotations

from _collections_abc import Mapping
from typing import Any

import pyproj
import xarray as xr
from xarray.indexes import Index


def _format_crs(crs: pyproj.CRS, max_width: int = 20) -> str:
    srs = crs.to_string()
    return srs if len(srs) <= max_width else " ".join([srs[:max_width], "..."])


class CRSIndex(Index):
    """A basic :py:class:`xarray.Index` that has a :py:class:`pyproj.crs.CRS`
    attached.

    This index must be associated with a scalar coordinate variable.

    Best way to create a CRSIndex is via either
    :py:meth:`xarray.Dataset.proj.assign_crs` or
    :py:meth:`xarray.Dataset.set_xindex` (or the DataArray equivalent methods).

    This index is used for propagation of the CRS information through Xarray
    operations and for CRS-aware alignment of Xarray objects (only checking
    strict equality, automatic re-indexing / re-projection is not supported). It
    doesn't support CRS-aware data selection.

    """

    _crs: pyproj.CRS

    def __init__(self, crs: pyproj.CRS | Any):
        """
        Parameters
        ----------
        crs : Any
            The coordinate reference system to attach to the index in any format
            that can be passed to :py:meth:`pyproj.crs.CRS.from_user_input`.

        """
        self._crs = pyproj.CRS.from_user_input(crs)

    @property
    def crs(self) -> pyproj.CRS:
        """Returns the :py:class:`pyproj.crs.CRS` object attached to this index."""
        return self._crs

    @classmethod
    def from_variables(
        cls,
        variables: Mapping[Any, xr.Variable],
        *,
        options: Mapping[str, Any],
    ) -> CRSIndex:
        if len(variables) != 1:
            raise ValueError("can only create a CRSIndex from one scalar variable")

        var = next(iter(variables.values()))

        if var.ndim != 0:
            raise ValueError("can only create a CRSIndex from one scalar variable")

        # TODO: how to deal with different CRS in var attribute vs. build option?
        crs = var.attrs.get("spatial_ref", options["crs"])

        return cls(crs)

    def equals(self, other: CRSIndex) -> bool:
        if not isinstance(other, CRSIndex):
            return False
        if not self.crs == other.crs:
            return False
        return True

    def _repr_inline_(self, max_width: int) -> str:
        if max_width is None:
            max_width = xr.get_options()["display_width"]

        srs = _format_crs(self.crs, max_width=max_width)
        return f"{self.__class__.__name__} (crs={srs})"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}" + "\n" + repr(self.crs)
