from __future__ import annotations

import warnings
from collections.abc import Hashable, Iterable, Mapping
from typing import Any, Literal, TypeVar, cast

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

        if not accessor_names[xr.Dataset] and not accessor_names[xr.DataArray]:
            raise ValueError(
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


def register_accessor(accessor_cls: T_AccessorClass) -> T_AccessorClass:
    """Decorator for registering a geospatial, CRS-dependent Xarray
    (Dataset and/or DataArray) accessor.

    Parameters
    ----------
    accessor_cls : class
        A Python class that has been decorated with
        :py:func:`xarray.register_dataset_accessor` and/or
        :py:func:`xarray.register_dataarray_accessor`.
        It is important that this decorator is applied on top of
        those Xarray decorators.

    """

    GeoAccessorRegistry.register_accessor(accessor_cls)
    return accessor_cls


class CRSProxy:
    """A proxy for a CRS(-aware) indexed coordinate."""

    _obj: xr.Dataset | xr.DataArray
    _crs_coord_name: Hashable
    _crs: pyproj.CRS

    def __init__(self, obj: xr.Dataset | xr.DataArray, coord_name: Hashable, crs: pyproj.CRS):
        self._obj = obj
        self._crs_coord_name = coord_name
        self._crs = crs

    @property
    def crs(self) -> pyproj.CRS:
        """Return the coordinate reference system as a :class:`pyproj.CRS` object."""
        return self._crs


@xr.register_dataset_accessor("proj")
@xr.register_dataarray_accessor("proj")
class ProjAccessor:
    """Xarray `.proj` extension entry-point."""

    _obj: xr.Dataset | xr.DataArray
    _crs_indexes: dict[Hashable, CRSIndex] | None
    _crs_aware_indexes: dict[Hashable, xr.Index] | None
    _crs: pyproj.CRS | None | Literal[False]

    def __init__(self, obj: xr.Dataset | xr.DataArray):
        self._obj = obj
        self._crs_indexes = None
        self._crs_aware_indexes = None
        self._crs = False

    def _cache_all_crs_indexes(self):
        # get both CRSIndex objects and CRS-aware Index objects in cache
        self._crs_indexes = {}
        self._crs_aware_indexes = {}

        for idx, vars in self._obj.xindexes.group_by_index():
            if isinstance(idx, CRSIndex):
                name = next(iter(vars))
                self._crs_indexes[name] = idx
            elif hasattr(idx, "_proj_get_crs"):
                for name in vars:
                    self._crs_aware_indexes[name] = idx

    @property
    def crs_indexes(self) -> Frozen[Hashable, CRSIndex]:
        """Return an immutable dictionary of coordinate names as keys and
        :py:class:`~xproj.CRSIndex` objects as values.

        Return an empty dictionary if no coordinate with a CRSIndex is found.

        Otherwise return a dictionary with a single entry or raise an error if
        multiple coordinates with a CRSIndex are found (currently not
        supported).

        """
        if self._crs_indexes is None:
            self._cache_all_crs_indexes()

        return FrozenDict(self._crs_indexes)

    @property
    def crs_aware_indexes(self) -> Frozen[Hashable, xr.Index]:
        """Return an immutable dictionary of coordinate names as keys and
        xarray Index objects that are CRS-aware.

        An :py:class:`xarray.Index` is CRS-aware if it implements XProj's CRS
        interface, i.e., at least implements a method like
        :py:meth:`~xproj.ProjIndexMixin._proj_get_crs`.

        """
        if self._crs_aware_indexes is None:
            self._cache_all_crs_indexes()

        return FrozenDict(self._crs_aware_indexes)

    def __call__(self, coord_name: Hashable):
        """Select a given CRS by coordinate name.

        Parameter
        ---------
        coord_name : Hashable
            Either the name of a (scalar) spatial reference coordinate with a
            :py:class:`~xproj.CRSIndex` or the name of a coordinate with an
            index that implements XProj's CRS interface.

        Returns
        -------
        proxy
            A proxy accessor for a single CRS.

        """
        if coord_name in self.crs_aware_indexes:
            index = self.crs_aware_indexes[coord_name]
            return CRSProxy(self._obj, coord_name, index._proj_get_crs())  # type: ignore

        if coord_name not in self.crs_indexes:
            if coord_name not in self._obj.coords:
                raise KeyError(f"no coordinate {coord_name!r} found in Dataset or DataArray")
            elif coord_name not in self._obj.xindexes:
                raise ValueError(f"coordinate {coord_name!r} has no index")
            else:
                raise ValueError(f"coordinate {coord_name!r} index is not a CRSIndex")

        return CRSProxy(self._obj, coord_name, self.crs_indexes[coord_name].crs)

    def assert_one_crs_index(self):
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
    def crs(self) -> pyproj.CRS | None:
        """Return the coordinate reference system as a :py:class:`pyproj.crs.CRS`
        object, or ``None`` if there isn't any.

        """
        if self._crs is False:
            all_crs = {name: idx.crs for name, idx in self.crs_indexes.items()}
            for name, idx in self.crs_aware_indexes.items():
                crs = idx._proj_get_crs()  # type: ignore
                if crs is not None:
                    all_crs[name] = crs

            if not all_crs:
                self._crs = None
            elif len(set(all_crs.values())) == 1:
                self._crs = next(iter(all_crs.values()))
            else:
                raise ValueError(
                    "found multiple CRS in Dataset or DataArray:\n"
                    + "\n".join(f"{name}: {crs.to_string()}" for name, crs in all_crs.items())
                )

        return self._crs  # type: ignore

    def assign_crs(
        self,
        coord_name_crs: Mapping[Hashable, Any] | None = None,
        allow_override: bool = False,
        **coord_name_crs_kwargs: Any,
    ) -> xr.DataArray | xr.Dataset:
        """Set the coordinate reference system (CRS) attached to a scalar coordinate.

        Doesn't trigger any coordinate transformation or data resampling.

        Parameters
        ----------
        coord_name_crs : dict-like or None, optional
            A dict where the keys are the names of the (scalar) coordinates and values
            target CRS in any format accepted by
            :meth:`pyproj.CRS.from_user_input() <pyproj.crs.CRS.from_user_input>` such
            as an authority string (e.g. ``"EPSG:4326"``), EPSG code (e.g. ``4326``) or
            a WKT string.
            If the coordinate(s) doesn't exist it will be created.
            Only one item is currently allowed.
        allow_override : bool, default False
            Allow to replace the index if the coordinates already have an index.
        **coord_names_crs_kwargs : optional
            The keyword arguments form of ``coord_name_crs``.
            One of ``coord_name_crs`` or ``coord_name_crs_kwargs`` must be provided.

        """
        coord_name_crs = either_dict_or_kwargs(coord_name_crs, coord_name_crs_kwargs, "set_crs")

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

            # 3rd-party geospatial accessor hooks
            for accessor_obj in GeoAccessorRegistry.get_accessors(_obj):
                if hasattr(accessor_obj, "_proj_set_crs"):
                    _obj = accessor_obj._proj_set_crs(name, crs)

        return _obj

    def map_crs(
        self,
        crs_coord_to_coords: Mapping[Hashable, Iterable[Hashable]] | None = None,
        **crs_coord_to_coords_kwargs: Any,
    ) -> xr.DataArray | xr.Dataset:
        """Map spatial reference coordinate(s) to other indexed coordinates.

        Parameters
        ----------
        crs_coord_to_coords : dict, optional
            A dict where the keys are the names of (scalar) spatial reference
            coordinates and values are the names of other coordinates with an index.
        **coord_names_crs_kwargs : optional
            The keyword arguments form of ``crs_coord_to_coords``.
            One of ``crs_coord_to_coords`` or ``coord_name_crs_kwargs`` must be provided.

        """
        crs_coord_to_coords = either_dict_or_kwargs(
            crs_coord_to_coords, crs_coord_to_coords_kwargs, "map_crs"
        )

        _obj = self._obj.copy(deep=False)
        indexes = _obj.xindexes

        for crs_coord_name, coord_names in crs_coord_to_coords.items():
            crs = self(crs_coord_name).crs

            map_indexes = []
            map_indexes_coords = set()

            for name in coord_names:
                if name in map_indexes_coords:
                    continue
                if name not in _obj.coords:
                    raise KeyError(f"no coordinate {name!r} found in Dataset or DataArray")
                elif name not in indexes:
                    raise KeyError(
                        f"no index found in Dataset or DataArray for coordinate {name!r}"
                    )

                map_indexes.append(indexes[name])
                map_indexes_coords.update(set(indexes.get_all_coords(name)))

            # must explicitly provide all coordinates of each found index
            missing_coords = map_indexes_coords - set(coord_names)
            if missing_coords:
                raise ValueError(
                    f"missing indexed coordinate(s) to map to the {crs_coord_name!r} spatial "
                    f"reference coordinate: {tuple(missing_coords)}"
                )

            for index, vars in indexes.group_by_index():
                if index not in map_indexes:
                    continue
                if not hasattr(index, "_proj_set_crs"):
                    warnings.warn(
                        f"the index of coordinates {tuple(vars)} doesn't implement the "
                        "`_proj_set_crs` interface, `map_crs()` won't have any effect.",
                        UserWarning,
                    )
                else:
                    new_index = index._proj_set_crs(crs_coord_name, crs)  # type: ignore
                    new_vars = new_index.create_variables(vars)
                    _obj = _obj.assign_coords(
                        xr.Coordinates(new_vars, {n: new_index for n in vars})
                    )

        return _obj
