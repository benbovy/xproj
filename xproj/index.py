from __future__ import annotations

from typing import Any, Hashable, Mapping

import pyproj
import xarray as xr
from xarray.indexes import Index


def _format_crs(crs: pyproj.CRS | None, max_width: int = 20) -> str:
    if crs is not None:
        srs = crs.to_string()
    else:
        srs = "None"

    return srs if len(srs) <= max_width else " ".join([srs[:max_width], "..."])


class CRSIndex(Index):

    _crs: pyproj.CRS | None
    _coord_names: list[Hashable]

    def __init__(self, crs: pyproj.CRS | None = None):
        if crs is not None:
            crs = pyproj.CRS.from_user_input(crs)

        self._crs = crs
        self._coord_names = []

    @property
    def crs(self) -> pyproj.CRS | None:
        return self._crs

    @property
    def coord_names(self) -> list[Hashable]:
        return self.coord_names

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
        crs = var.attrs.get("spatial_ref", options.get("crs"))

        return cls(crs=crs)

    def _check_crs(self, other_crs: pyproj.CRS | None, allow_none: bool = False) -> bool:
        """Check if the index's projection is the same than the given one.
        If allow_none is True, empty CRS is treated as the same.
        """
        if allow_none:
            if self.crs is None or other_crs is None:
                return True
        if not self.crs == other_crs:
            return False
        return True

    def equals(self, other: CRSIndex) -> bool:
        if not isinstance(other, CRSIndex):
            return False
        if not self._check_crs(other.crs, allow_none=True):
            return False
        return True

    def _repr_inline_(self, max_width: int) -> str:
        # TODO: remove when fixed in XArray
        if max_width is None:
            max_width = xr.get_options()["display_width"]

        srs = _format_crs(self.crs, max_width=max_width)
        return f"{self.__class__.__name__} (crs={srs})"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}" + "\n" + repr(self.crs)
