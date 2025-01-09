(terminology)=

# Terminology

:::{glossary}

CRS
   A Coordinate Reference System defines how coordinate labels are related
   to real locations on Earth. XProj uses {class}`pyproj.crs.CRS` objects
   to handle those reference systems.

Spatial reference coordinate
   An Xarray scalar {term}`coordinate` that usually declares a specific
   {term}`CRS` via its metadata. CF conventions use the term [grid mapping
   variable](https://cfconventions.org/Data/cf-conventions/cf-conventions-1.12/cf-conventions.html#grid-mappings-and-projections)
   for almost the same concept (the only difference is that a *grid mapping
   variable* is a data variable, not a coordinate, although Xarray's builtin CF
   decoders automatically promote it as a coordinate). XProj associates a
   {class}`~xproj.CRSIndex` to such coordinate. The name and the value of the
   coordinate is arbitrary, although ``spatial_ref`` is a common name used by
   default in [rioxarray](https://corteva.github.io/rioxarray) and
   [odc-geo](https://odc-geo.readthedocs.io) (inspired by GDAL).

CRS-aware index
   Any custom {class}`xarray.Index` that implements data selection, alignment
   and/or other functionality that depends on a {term}`CRS`. It is usually
   associated with one or more Xarray {term}`coordinate` variables with spatial
   labels (e.g., x/y or latitude/longitude grid point labels, ``shapely.Geometry``
   features, etc.). It is distinct from a {class}`~xproj.CRSIndex`, which is
   exclusively associated with a {term}`spatial reference coordinate`. XProj
   identifies an Xarray index as CRS-aware if the latter implements the
   {term}`proj index interface`.

Proj index interface
   A set of XProj-specific "hook" methods that can be implemented in a
   {term}`CRS-aware index` and that allow executing custom logic (e.g.,
   coordinate transformation) or updating the internal state of the index via
   XProj's public API. It is also used by XProj to access the index's
   {term}`CRS`. The index interface is defined in
   {class}`~xproj.ProjIndexMixin`, although it is not required for an Xarray
   Index to inherit from this mixin class.

Proj accessor interface
   A set of XProj-specific "hook" methods that can be implemented in an Xarray
   Dataset or DataArray accessor and that allow executing custom logic (e.g.,
   re-projection) or updating the internal state of the accessor via XProj's
   public API. The proj accessor interface is defined in
   {class}`~xproj.ProjAccessorMixin`, from which the accessor class should
   inherit.

:::
