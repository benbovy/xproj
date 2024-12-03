from __future__ import annotations

from collections.abc import Hashable, Mapping
from typing import Any, cast

import pyproj
import xarray as xr

from xproj.index import CRSIndex
from xproj.utils import Frozen, FrozenDict


def either_dict_or_kwargs(
    positional: Mapping[Any, Any] | None,
    keyword: Mapping[str, Any],
    func_name: str,
) -> Mapping[Hashable, Any]:
    """Resolve combination of positional and keyword arguments.

    Based on xarray's ``either_dict_or_kwargs``.
    """
    if positional and keyword:
        raise ValueError(
            "Cannot specify both keyword and positional arguments to " f"'.proj.{func_name}'."
        )
    if positional is None or positional == {}:
        return cast(Mapping[Hashable, Any], keyword)
    return positional


def get_crs_indexes(
    xr_obj: xr.Dataset | xr.DataArray,
    coord_name: Hashable | None = None,
) -> dict[Hashable, CRSIndex]:
    """Find the coordinates with a CRSIndex in a Dataset or DataArray.

    Return an empty dictionary if no such indexed coordinate is found.

    Currently raise an error if multiple coordinates are found in the
    same Dataset or DataArray (currently not supported).

    """
    if coord_name is not None:
        if coord_name not in xr_obj.coords:
            raise KeyError(f"no coordinate {coord_name!r} found in Dataset or DataArray")

        indexes = xr_obj.xindexes
        if coord_name not in indexes:
            raise ValueError(f"coordinate {coord_name!r} has no index")

        index = indexes[coord_name]
        if not isinstance(index, CRSIndex):
            raise ValueError(f"coordinate {coord_name!r} index is not a CRSIndex")

        return {coord_name: index}

    else:
        crs_indexes = {}
        for idx, vars in xr_obj.xindexes.group_by_index():
            if isinstance(idx, CRSIndex):
                coord_name = next(iter(vars))
                crs_indexes[coord_name] = idx

        if len(crs_indexes) > 1:
            raise ValueError(
                "found more than one coordinate with a CRSIndex in Dataset or DataArray "
                "(currently not supported)"
            )

        return crs_indexes


@xr.register_dataset_accessor("proj")
@xr.register_dataarray_accessor("proj")
class _ProjAccessor:
    """Xarray `.proj` extension entry-point."""

    _obj: xr.Dataset | xr.DataArray
    _crs_indexes = dict[Hashable, CRSIndex] | None

    def __init__(
        self, obj: xr.Dataset | xr.DataArray, crs_indexes: dict[Hashable, CRSIndex] | None = None
    ):
        self._obj = obj
        self._crs_indexes = crs_indexes

    @property
    def crs_indexes(self) -> Frozen[Hashable, CRSIndex]:
        """Return an immutable dictionary of coordinate names as keys and
        CRSIndex objects as values.

        Return an empty dictionary if no coordinate with a CRSIndex is found.

        Otherwise return a dictionary with a single entry or raise an error if
        multiple coordinates with a CRSIndex are found (currently not
        supported).

        """
        if self._crs_indexes is None:
            self._crs_indexes = get_crs_indexes(self._obj)
        return FrozenDict(self._crs_indexes)

    def __call__(self, coord_name: Hashable | None = None):
        # So we can use the extension by passing a coordinate name,
        # e.g., `ds.proj("spatial_ref").crs`
        # -> slightly faster than parsing all coordinates and their indexes
        # -> useful in case users want to write more explicit & readable code
        # -> may be useful if we eventually allow multiple CRSs per Dataset or DataArray
        if coord_name is None:
            return self
        else:
            crs_indexes = get_crs_indexes(self._obj, coord_name=coord_name)
            return _ProjAccessor(self._obj, crs_indexes=crs_indexes)

    @property
    def crs(self) -> pyproj.CRS | None:
        """Return the coordinate reference system as a :class:`pyproj.CRS`
        object, or `None` if there isn't any.

        """
        indexes = self.crs_indexes
        if not indexes:
            return None
        else:
            index = next(iter(indexes.values()))
            return index.crs

    def set_crs(
        self,
        coord_name_crs: Mapping[Hashable, Any] | None = None,
        allow_override: bool = False,
        **coord_name_crs_kwargs: Any,
    ) -> xr.DataArray | xr.Dataset:
        """Set the coordinate reference system (CRS) attached to a scalar coordinate.

        Currently supports setting only one CRS.
        Doesn't trigger any coordinate transformation or data resampling.

        Parameters
        ----------
        coord_name_crs : dict-like or None, optional
            A dict where the keys are the names of the (scalar) coordinates and values
            target CRS in any format accepted by
            :meth:`pyproj.CRS.from_user_input() <pyproj.crs.CRS.from_user_input>` such
            as an authority string (e.g. ``"EPSG:4326"``), EPSG code (e.g. ``4326``) or
            a WKT string.
            If the coordinate(s) doesn't exist they will be created.
            Only one item is currently allowed.
        allow_override : bool, default False
            Allow to replace the index if the coordinates already have an index.
        **coord_names_crs_kwargs : optional
            The keyword arguments form of ``coord_name_crs``.
            One of ``coord_name_crs`` or ``coord_name_crs_kwargs`` must be provided.

        """
        coord_name_crs = either_dict_or_kwargs(coord_name_crs, coord_name_crs_kwargs, "set_crs")

        if len(coord_name_crs) > 1:
            raise ValueError("setting multiple CRSs is currently not supported.")

        _obj = self._obj.copy(deep=False)

        for name, crs in coord_name_crs.items():
            if name not in _obj.coords:
                _obj.coords[name] = 0
            if not allow_override and name in _obj.xindexes:
                raise ValueError(
                    f"coordinate {name!r} already has an index. "
                    "Specify 'allow_override=True' to allow replacing it."
                )
            _obj = _obj.drop_indexes(name).set_xindex(str(name), CRSIndex, crs=crs)

        return _obj
