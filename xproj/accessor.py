from __future__ import annotations

from collections.abc import Hashable, Mapping
from typing import Any, TypeVar, cast

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

        return crs_indexes


class GeoAccessorRegistry:
    """A registry of 3rd-party geospatial Xarray accessors."""

    _accessor_names: dict[type[xr.Dataset] | type[xr.DataArray], set[str]] = {
        xr.Dataset: set(),
        xr.DataArray: set(),
    }

    @classmethod
    def register_accessor(cls, accessor_cls: Any):
        accessor_names = {}

        for xr_cls in (xr.Dataset, xr.DataArray):
            accessor_names[xr_cls] = {n for n in dir(xr_cls) if getattr(xr_cls, n) is accessor_cls}

        if not accessor_names:
            raise KeyError(
                f"class {accessor_cls.__name__} is not an Xarray Dataset or DataArray "
                "accessor decorated class"
            )

        for xr_cls, names in accessor_names.items():
            cls._accessor_names[xr_cls].update(names)

    @classmethod
    def get_accessors(cls, xr_obj: xr.Dataset | xr.DataArray) -> list[Any]:
        accessors = []

        for name in cls._accessor_names[type(xr_obj)]:
            accessor_obj = getattr(xr_obj, name, None)
            if accessor_obj is not None and not isinstance(accessor_obj, xr.DataArray):
                accessors.append(accessor_obj)

        return accessors


T_AccessorClass = TypeVar("T_AccessorClass")


def register_geoaccessor(accessor_cls: T_AccessorClass) -> T_AccessorClass:
    """Register a geospatial, CRS-dependent Xarray (Dataset and/or DataArray) accessor."""

    GeoAccessorRegistry.register_accessor(accessor_cls)
    return accessor_cls


class CRSAccessor:
    """Xarray extension entry-point for a single CRS."""

    _obj: xr.Dataset | xr.DataArray
    _crs_coord_name: Hashable
    _crs_index: CRSIndex

    def __init__(self, obj: xr.Dataset | xr.DataArray, coord_name: Hashable, index: CRSIndex):
        self._obj = obj

        # crs_indexes = get_crs_indexes(obj, coord_name=coord_name)
        # assert len(crs_indexes) == 1
        self._crs_coord_name = coord_name
        self._crs_index = index

    @property
    def crs(self) -> pyproj.CRS:
        """Return the coordinate reference system as a :class:`pyproj.CRS` object."""
        return self._crs_index.crs


@xr.register_dataset_accessor("proj")
@xr.register_dataarray_accessor("proj")
class ProjAccessor:
    """Xarray `.proj` extension entry-point."""

    _obj: xr.Dataset | xr.DataArray
    _crs_indexes = dict[Hashable, CRSIndex] | None

    def __init__(self, obj: xr.Dataset | xr.DataArray):
        self._obj = obj
        self._crs_indexes = None

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

    def __call__(self, coord_name: Hashable):
        """Select a given CRS by coordinate name.

        Parameter
        ---------
        coord_name : Hashable
            The name of a (scalar) spatial reference coordinate, which
            must have a CRSIndex.

        Returns
        -------
        crs_accessor
            A Xarray Dataset or DataArray accessor for a single CRS.

        """
        # TODO: only one CRS per Dataset / DataArray -> maybe remove this restriction later
        # (https://github.com/benbovy/xproj/issues/2)
        try:
            self.assert_single_crs()
        except AssertionError:
            raise ValueError(
                "found multiple coordinates with a CRSIndex in Dataset or DataArray "
                "(currently not supported)."
            )

        if coord_name not in self.crs_indexes:
            if coord_name not in self._obj.coords:
                raise KeyError(f"no coordinate {coord_name!r} found in Dataset or DataArray")
            elif coord_name not in self._obj.xindexes:
                raise ValueError(f"coordinate {coord_name!r} has no index")
            else:
                raise ValueError(f"coordinate {coord_name!r} index is not a CRSIndex")

        return CRSAccessor(self._obj, coord_name, self.crs_indexes[coord_name])

    def assert_single_crs(self):
        """Raise an `AssertionError` if no or multiple CRS-indexed coordinates
        are found in the Dataset or DataArray.
        """
        if len(self.crs_indexes) != 1:
            if not self.crs_indexes:
                msg = "no CRS found in Dataset or DataArray"
            else:
                msg = "multiple CRS found in Dataset or DataArray"
            raise AssertionError(msg)

    @property
    def _crs_index(self) -> CRSIndex | None:
        # return a CRSIndex if only one instance is found in Dataset or DataArray
        # return None if no such instance is found
        # raise an error if multiple instances are found
        indexes = self.crs_indexes
        if len(indexes) > 1:
            raise ValueError(
                "found multiple coordinates with a CRSIndex in Dataset or DataArray. "
                "Use instead `.proj('coord_name')` to a select a spatial reference coordinate."
            )
        elif len(indexes) == 1:
            return next(iter(indexes.values()))
        else:
            return None

    @property
    def crs(self) -> pyproj.CRS | None:
        """Return the coordinate reference system as a :class:`pyproj.CRS`
        object, or ``None`` if there isn't any.

        """
        crs_index = self._crs_index

        if crs_index is None:
            return None
        else:
            return crs_index.crs

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

        # TODO: only one CRS per Dataset / DataArray -> maybe remove this restriction later
        # (https://github.com/benbovy/xproj/issues/2)
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
            _obj = _obj.drop_indexes(name, errors="ignore").set_xindex(str(name), CRSIndex, crs=crs)

            for accessor_obj in GeoAccessorRegistry.get_accessors(_obj):
                if hasattr(accessor_obj, "__proj_set_crs__"):
                    _obj = accessor_obj.__proj_set_crs__(name, crs)

        return _obj
