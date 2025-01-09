---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.16.5
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

# Intergration With 3rd-Party Extensions

3rd-party Xarray geospatial extensions may leverage XProj in different ways:

- simply consume the API exposed via the {ref}`"proj" Dataset and DataArray
  accessors <proj_accessors>`.

- register a custom Xarray accessor that implements the {term}`proj accessor
  interface` (example below)

- implement one or more methods of the {term}`proj index interface` in a custom
  Xarray index (example below)

<br>

```{code-cell} ipython3
import pyproj
import xarray as xr
import xproj

xr.set_options(display_expand_indexes=True);
```

## CRS-aware Xarray accessor

Here below is a basic example of a custom "geo" Xarray Dataset accessor class
that is also explictly registered with the {func}`xproj.register_accessor`
decorator. It inherits from {class}`~xproj.ProjAccessorMixin`.

Registering this "geo" accessor allows executing custom logic from within the
accessor (via the {term}`proj accessor interface`) when calling `xproj` API.

:::{note}
The {func}`xproj.register_accessor` decorator must be applied after (on top of)
the Xarray register decorators.
:::


```{code-cell} ipython3
@xproj.register_accessor
@xr.register_dataset_accessor("geo")
class GeoAccessor(xproj.ProjAccessorMixin):

    def __init__(self, obj):
        self._obj = obj

    @property
    def crs(self):
        # Just reusing XProj's API
        # (Assuming this accessor only supports single-CRS datasets)
        return self._obj.proj.crs

    def _proj_set_crs(self, crs_coord_name, crs):
        # Nothing much done here, just printing something before
        # returning the Xarray dataset unchanged

        print(f"from GeoAccessor: new CRS of {crs_coord_name!r} is {crs}!")
        return self._obj
```

Let's see it in action with an Xarray tutorial dataset.

```{code-cell} ipython3
ds = xr.tutorial.load_dataset("air_temperature")
```

Assigning a new {term}`spatial reference coordinate` with a CRS will also call
the ``GeoAccessor._proj_set_crs`` method implemented above.

```{code-cell} ipython3
ds_wgs84 = ds.proj.assign_crs(spatial_ref="epsg:4326")
```

```{code-cell} ipython3
ds_wgs84
```

The CRS defined above can be accessed via the "geo" accessor:

```{code-cell} ipython3
ds_wgs84.geo.crs
```

## CRS-aware Xarray index

Here below is a basic example of a {term}`CRS-aware index`, i.e., a custom
Xarray index that adds some CRS-dependent functionality (via the {term}`proj
index interface`) on top of Xarray's default `PandasIndex`.

:::{note}
The {class}`~xproj.ProjIndexMixin` class can be used to mark an Xarray index as
formally implementing the {term}`proj index interface`. However, XProj doesn't
require an Xarray index to explicitly inherit from this mixin class to be
recognized as CRS-aware.
:::

```{code-cell} ipython3
import warnings


class GeoIndex(xr.indexes.PandasIndex, xproj.ProjIndexMixin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._crs = None

    def sel(self, *args, **kwargs):
        if self._crs is not None:
            warnings.warn(
                f"make sure that indexer labels have CRS {self._crs}!",
                UserWarning,
            )

        return super().sel(*args, **kwargs)

    def _proj_get_crs(self):
        return self._crs

    def _proj_set_crs(self, spatial_ref, crs):
        # note: `spatial_ref` is not used here
        print(f"set CRS of index {self!r} to crs={crs}!")

        self._crs = crs
        return self

    def _copy(self, deep=True, memo=None):
        # bug in PandasIndex? crs attribute not copied here
        obj = super()._copy(deep=deep, memo=memo)
        obj._crs = self._crs
        return obj

    def _repr_inline_(self, max_width=70):
        return f"{type(self).__name__} (crs={self._crs})"

    def __repr__(self):
        return f"{type(self).__name__} (crs={self._crs})"
```

Let's see it in action by reusing the example dataset above, to which we replace
the default indexes of the "lat" and "lon" coordinates with instances of the
``GeoIndex`` defined above.

```{code-cell} ipython3
ds_geo_wgs84 = (
    ds_wgs84
    .drop_indexes(["lat", "lon"])
    .set_xindex("lat", GeoIndex)
    .set_xindex("lon", GeoIndex)
)
```

Note that the CRS of the "lat" and "lon" indexes aren't yet initialized despite
the presence of the "spatial_ref" coordinate:

```{code-cell} ipython3
ds_geo_wgs84
```

Mapping the CRS of "spatial_ref" to the "lat" and "lon" geo-indexed coordinates has
to be done manually using {meth}`xarray.Dataset.proj.map_crs`:

```{code-cell} ipython3
ds_geo_wgs84 = ds_geo_wgs84.proj.map_crs(spatial_ref=["lat", "lon"])
```

The CRS of the "lat" and "lon" geo-indexed coordinates is updated via the
{term}`proj index interface` implemented in ``GeoIndex``. Data selection is now
CRS-aware! (just a warning is emitted below).

```{code-cell} ipython3
ds_geo_wgs84.sel(lat=70)
```

Since ``GeoIndex`` also implements the ``_proj_get_crs`` method it is possible
to get the CRS from the "lat" coordinate like so:

```{code-cell} ipython3
ds_geo_wgs84.proj("lat").crs
```

### Caveat

Changing the CRS of a {term}`spatial reference coordinate` via
{meth}`~xarray.Dataset.proj.assign_crs()` requires to manually call
{meth}`~xarray.Dataset.proj.map_crs()` again in order to synchronize the new CRS
with the coordinate indexes.

```{code-cell} ipython3
temp = ds_geo_wgs84.proj.assign_crs(spatial_ref="epsg:4322", allow_override=True)

# note the CRS of the "lat" and "lon" indexes that hasn't changed
temp
```

```{code-cell} ipython3
ds_geo_wgs72 = temp.proj.map_crs(spatial_ref=["lat", "lon"], allow_override=True)

# up-to-date CRS
ds_geo_wgs72
```
