from __future__ import annotations

import warnings
from collections.abc import Callable, Hashable, Iterable, Mapping
from typing import Any, Literal, TypeVar, cast

import pyproj
import xarray as xr

from xproj.crs_utils import format_compact_cf
from xproj.index import CRSIndex
from xproj.mixins import ProjIndexMixin
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
            f"Cannot specify both keyword and positional arguments to '.proj.{func_name}'."
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


def is_crs_aware(index: xr.Index) -> bool:
    return isinstance(index, ProjIndexMixin) or hasattr(index, "_proj_get_crs")


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
            elif is_crs_aware(idx):
                for name in vars:
                    self._crs_aware_indexes[name] = idx

    @property
    def crs_indexes(self) -> Frozen[Hashable, CRSIndex]:
        """Return an immutable dictionary of coordinate names as keys and
        :py:class:`~xproj.CRSIndex` objects as values.

        Return an empty dictionary if no coordinate with a CRSIndex is found.

        """
        if self._crs_indexes is None:
            self._cache_all_crs_indexes()

        return FrozenDict(self._crs_indexes)

    @property
    def crs_aware_indexes(self) -> Frozen[Hashable, xr.Index]:
        """Return an immutable dictionary of coordinate names as keys and
        xarray Index objects that are CRS-aware.

        A :term:`CRS-aware index` is an :py:class:`xarray.Index` object that
        must at least implements a method like
        :py:meth:`~xproj.ProjIndexMixin._proj_get_crs`.

        """
        if self._crs_aware_indexes is None:
            self._cache_all_crs_indexes()

        return FrozenDict(self._crs_aware_indexes)

    def _get_crs_index(self, coord_name: Hashable) -> CRSIndex:
        # Get a nice error message when trying to access a spatial reference
        # coordinate with a CRSIndex using an arbitrary name.

        if coord_name not in self.crs_indexes:
            if coord_name not in self._obj.coords:
                raise KeyError(f"no coordinate {coord_name!r} found in Dataset or DataArray")
            elif self._obj.coords[coord_name].ndim != 0:
                raise ValueError(f"coordinate {coord_name!r} is not a scalar coordinate")
            elif coord_name not in self._obj.xindexes:
                raise ValueError(
                    f"coordinate {coord_name!r} has no index. It must have a CRSIndex associated "
                    f"(e.g., via Dataset.proj.assign_crs({coord_name}=...) or "
                    f"DataArray.proj.assign_crs({coord_name}=...)) to be used as "
                    "a spatial reference coordinate with xproj."
                )
            else:
                raise ValueError(f"coordinate {coord_name!r} index is not a CRSIndex")

        return self.crs_indexes[coord_name]

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
        crs: pyproj.CRS

        if coord_name in self.crs_aware_indexes:
            crs = self.crs_aware_indexes[coord_name]._proj_get_crs()  # type: ignore
        else:
            crs = self._get_crs_index(coord_name).crs

        return CRSProxy(self._obj, coord_name, crs)

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

        Raises an error if multiple CRS are found in the Dataset or DataArray.

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
        spatial_ref_crs: Mapping[Hashable, Any] | None = None,
        allow_override: bool = False,
        **spatial_ref_crs_kwargs: Any,
    ) -> xr.DataArray | xr.Dataset:
        """Assign one or more spatial reference coordinate variables, each with
        a given coordinate reference system (CRS).

        Doesn't trigger any coordinate transformation or data resampling.

        Parameters
        ----------
        spatial_ref_crs : dict-like or None, optional
            A dict where the keys are the names of the (scalar) coordinate variables
            and values target CRS in any format accepted by
            :meth:`pyproj.CRS.from_user_input() <pyproj.crs.CRS.from_user_input>` such
            as an authority string (e.g. ``"EPSG:4326"``), EPSG code (e.g. ``4326``) or
            a WKT string.
            If the coordinate(s) doesn't exist it will be created.
        allow_override : bool, default False
            Allow to replace the index if the coordinates already have an index.
        **spatial_ref_crs_kwargs : optional
            The keyword arguments form of ``spatial_ref_crs``.
            One of ``spatial_ref_crs`` or ``spatial_ref_crs_kwargs`` must be provided.

        Returns
        -------
        Dataset or DataArray
            A new Dataset or DataArray object with new or updated
            :term:`spatial reference coordinate` variables.

        """
        spatial_ref_crs = either_dict_or_kwargs(
            spatial_ref_crs, spatial_ref_crs_kwargs, "assign_crs"
        )

        _obj = self._obj.copy(deep=False)

        for name, crs in spatial_ref_crs.items():
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
        spatial_ref_coords: Mapping[Hashable, Iterable[Hashable]] | None = None,
        allow_override: bool = False,
        transform: bool = False,
        **spatial_ref_coords_kwargs: Any,
    ) -> xr.DataArray | xr.Dataset:
        """Map spatial reference coordinate(s) to other indexed coordinates.

        This has an effect only if the latter coordinates have a
        :term:`CRS-aware index`. The index must then support setting the CRS via
        the :term:`proj index interface`.

        Parameters
        ----------
        spatial_ref_coords : dict, optional
            A dict where the keys are the names of (scalar) spatial reference
            coordinates and values are the names of other coordinates with an index.
        allow_override : bool, optional
            If True, replace the CRS of the target index(es) even if they already have
            a CRS defined (default: False).
        transform : bool, optional
            If True (default: False), transform coordinate data to conform to the new CRS.
        **spatial_ref_coords_kwargs : optional
            The keyword arguments form of ``spatial_ref_coords``.
            One of ``spatial_ref_coords`` or ``spatial_ref_coords_kwargs`` must be provided.

        Returns
        -------
        Dataset or DataArray
            A new Dataset or DatArray object with updated CRS-aware indexes (and possibly
            updated coordinate data).

        """
        spatial_ref_coords = either_dict_or_kwargs(
            spatial_ref_coords, spatial_ref_coords_kwargs, "map_crs"
        )

        _obj = self._obj.copy(deep=False)
        indexes = _obj.xindexes

        for spatial_ref, coord_names in spatial_ref_coords.items():
            crs = self._get_crs_index(spatial_ref).crs

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
                    f"missing indexed coordinate(s) to map to the {spatial_ref!r} spatial "
                    f"reference coordinate: {tuple(missing_coords)}"
                )

            for index, vars in indexes.group_by_index():
                if index not in map_indexes:
                    continue
                if not is_crs_aware(index):
                    warnings.warn(
                        f"the index of coordinates {tuple(vars)} is not recognized as CRS-aware "
                        "by Xproj. `map_crs()` won't have any effect.",
                        UserWarning,
                    )
                    continue

                index_crs = index._proj_get_crs()  # type: ignore

                if not allow_override:
                    if index_crs is not None and index_crs != crs:
                        raise ValueError(
                            f"the index of coordinates {tuple(vars)} already has a CRS {index_crs} "
                            f"that is different than the spatial reference coordinate CRS {crs} "
                            "and allow_override=False"
                        )

                if index_crs == crs:
                    continue

                if transform and index_crs is not None:
                    index_update_crs_func = getattr(index, "_proj_to_crs")
                else:
                    index_update_crs_func = getattr(index, "_proj_set_crs")

                new_index = index_update_crs_func(spatial_ref, crs)
                new_vars = new_index.create_variables(vars)
                _obj = _obj.assign_coords(xr.Coordinates(new_vars, {n: new_index for n in vars}))

        return _obj

    def _update_crs_info(
        self, spatial_ref: Hashable | None, func: Callable[[xr.Variable, CRSIndex], None]
    ) -> xr.DataArray | xr.Dataset:
        if spatial_ref is None:
            spatial_ref_coords = list(self.crs_indexes)
        else:
            spatial_ref_coords = [spatial_ref]

        _obj = self._obj.copy(deep=False)

        for coord_name in spatial_ref_coords:
            index = self._get_crs_index(coord_name)
            var = self._obj[coord_name].variable.copy(deep=False)
            func(var, index)
            _obj = _obj.assign_coords(xr.Coordinates({coord_name: var}, {coord_name: index}))

        return _obj

    def write_crs_info(
        self,
        spatial_ref: Hashable | None = None,
        func: Callable[[pyproj.CRS], dict[str, Any]] = format_compact_cf,
    ) -> xr.DataArray | xr.Dataset:
        """Write CRS information as attributes to one or all spatial
        reference coordinates.

        Parameters
        ----------
        spatial_ref : Hashable, optional
            The name of a :term:`spatial reference coordinate`. If not provided (default),
            CRS information will be written to all spatial reference coordinates found in
            the Dataset or DataArray. Each spatial reference coordinate must already have
            a :py:class:`~xproj.CRSIndex` associated.
        func : callable, optional
            Any callable used to format CRS information as coordinate variable attributes.
            The default function adds a ``crs_wkt`` attribute for compatibility with
            CF conventions.

        Returns
        -------
        Dataset or DataArray
            A new Dataset or DatArray object with attributes updated for one or all
            spatial reference coordinates.

        See Also
        --------
        ~xproj.format_compact_cf
        ~xproj.format_full_cf_gdal
        Dataset.proj.clear_crs_info
        DataArray.proj.clear_crs_info

        """
        return self._update_crs_info(
            spatial_ref, lambda var, index: var.attrs.update(func(index.crs))
        )

    def clear_crs_info(self, spatial_ref: Hashable | None = None) -> xr.DataArray | xr.Dataset:
        """Convenient method to clear all attributes of one or all spatial
        reference coordinates.

        Parameters
        ----------
        spatial_ref : Hashable, optional
            The name of a :term:`spatial reference coordinate`. If not provided (default),
            CRS information will be cleared for all spatial reference coordinates found in
            the Dataset or DataArray. Each spatial reference coordinate must already have
            a :py:class:`~xproj.CRSIndex` associated.

        Returns
        -------
        Dataset or DataArray
            A new Dataset or DatArray object with attributes cleared for one or all
            spatial reference coordinates.

        See Also
        --------
        Dataset.proj.write_crs_info
        DataArray.proj.write_crs_info

        """
        return self._update_crs_info(spatial_ref, lambda var, _: var.attrs.clear())
