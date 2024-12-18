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

- simply consume the API exposed via the `.proj` Dataset / DataArray accessor,
  e.g., get the CRS using {attr}`xarray.Dataset.proj.crs`

- register a custom Xarray Dataset / DataArray accessor that also inherits from
  `xproj.ProjAccessorMixin` (example below)

- implement one or more methods of `xproj.ProjIndexMixin` in custom Xarray
  indexes (example below)

```{code-cell} ipython3
import pyproj
import xarray as xr
import xproj

xr.set_options(display_expand_indexes=True);
```

## CRS-aware Xarray accessor

Here below is a basic example of a custom Xarray Dataset accessor that is also
explictly registered as a "geo" accessor via the `xproj.register_accessor` class
decorator. Important note: the latter must be applied after (on top of) the
Xarray register decorators.

Registering this "geo" accessor allows executing custom logic from within the
accessor (via the CRS interface) when calling `xproj` API.

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

Let's see if it works as expected.

```{code-cell} ipython3
# create an empty dataset, The `.geo.crs` property is uninitialized

ds = xr.Dataset()

ds.geo.crs is None
```

```{code-cell} ipython3
# initialize the CRS via `.proj.assign_crs()`

ds_wgs84 = ds.proj.assign_crs(spatial_ref=pyproj.CRS.from_user_input("epsg:4326"))
```

```{code-cell} ipython3
ds_wgs84
```

```{code-cell} ipython3
# Access CRS via the `.geo` accessor

ds_wgs84.geo.crs
```

## CRS-aware Xarray index

Here below is a basic example of a custom Xarray index that adds some CRS-aware
functionality on top of Xarray's default `PandasIndex`.

```{code-cell} ipython3
import warnings


class GeoIndex(xr.indexes.PandasIndex, xproj.ProjIndexMixin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._crs = None

    def sel(self, *args, **kwargs):
        if self._crs is not None:
            warnings.warn(f"make sure that indexer labels have CRS {self._crs}!", UserWarning)

        return super().sel(*args, **kwargs)

    def _proj_get_crs(self):
        return self._crs

    def _proj_set_crs(self, crs_coord_name, crs):
        # `crs_coord_name` not used here (assuming single-CRS dataset)

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

Let's see how it works

```{code-cell} ipython3
# Create a new Dataset with a latitude coordinate and a (default) PandasIndex

ds = xr.Dataset({"lat": [1, 2, 3]})
ds
```

```{code-cell} ipython3
# Replace the PandasIndex with a GeoIndex (crs not yet initialized)

ds_geo = ds.drop_indexes(["lat"]).set_xindex("lat", GeoIndex)
ds_geo
```

```{code-cell} ipython3
# Initialize the CRS via `.proj.assign_crs()`

temp = ds_geo.proj.assign_crs(spatial_ref="epsg:4326")
temp
```

```{code-cell} ipython3
# Must explicitly map the spatial reference coordinate
# to the coordinate with a GeoIndex

ds_geo_wgs84 = temp.proj.map_crs(spatial_ref=["lat"])
```

```{code-cell} ipython3
# The index of the `lat` coordinate now has its CRS initialized!

ds_geo_wgs84
```

```{code-cell} ipython3
# "CRS-aware" data selection (just a warning emitted here)

ds_geo_wgs84.sel(lat=1)
```

Note: since `GeoIndex` implements the `_proj_get_crs` method it is also possible
to get the CRS from the "lat" coordinate like so:

```{code-cell} ipython3
ds_geo_wgs84.proj("lat").crs
```

### Caveat

Changing the CRS via `.proj.assign_crs()` requires to manually call
`.proj.map_crs()` again in order to synchronize the new CRS with the coordinate
index(es).

```{code-cell} ipython3
# Change CRS of "spatial_ref" (no effect on the GeoIndex of the "lat" coordinate!)

temp = ds_geo_wgs84.proj.assign_crs(spatial_ref="epsg:32662", allow_override=True)
temp
```

```{code-cell} ipython3
:tags: [raises-exception]

# Getting a unique CRS for the Dataset returns an error!

temp.proj.crs
```

```{code-cell} ipython3
# re-map "spatial_ref" to "lat"

ds_geo_plate_carree = temp.proj.map_crs(spatial_ref=["lat"])
ds_geo_plate_carree
```

```{code-cell} ipython3
# The latter Dataset now has a unique CRS

ds_geo_plate_carree.proj.crs
```
