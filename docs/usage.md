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

# Usage Examples

```{code-cell} ipython3
import numpy as np
import xarray as xr
import xproj

xr.set_options(display_expand_indexes=True);
```

## Example datasets

+++

- Dataset with no CRS attached

```{code-cell} ipython3
ds_vec = xr.Dataset(coords={"points": ("space", [1, 2, 3])})

ds_vec
```

## Set the CRS

`.proj.assign_crs()` can be used to set the CRS: it creates a new scalar
coordinate (if it doesn't exist yet) with a `xproj.CRSIndex`.

Note: the name of the spatial reference coordinate is arbitrary ("spatial_ref"
is a common name).

```{code-cell} ipython3
ds_wgs84 = ds_vec.proj.assign_crs(spatial_ref="epsg:4326")

ds_wgs84
```

## Get the CRS

+++

Via the `.proj.crs` property, which returns a
[pyproj.CRS](https://pyproj4.github.io/pyproj/stable/api/crs/crs.html) object.

```{code-cell} ipython3
ds_wgs84.proj.crs
```

Alternatively, it is possible to explicitly pass the CRS coordinate name to the
`.proj` accessor:

```{code-cell} ipython3
ds_wgs84.proj("spatial_ref").crs
```

## CRS-aware alignment

The index of the CRS coordinate is used to compare or align xarray objects based
on their CRS.

```{code-cell} ipython3
ds_pseudo_mercator = ds_wgs84.proj.assign_crs(spatial_ref="epsg:3857", allow_override=True)
```

Note the nice error message when trying to combine two datasets with different
CRS (only works if the CRS coordinates have the same name), raised by Xarray and
leveraging `pyproj.CRS`'s repr to output detailled information.

```{code-cell} ipython3
:tags: [raises-exception]

ds_wgs84 + ds_pseudo_mercator
```

This also works seamlessly with `xarray.concat()`:

```{code-cell} ipython3
xr.concat([ds_wgs84.isel(space=[0, 1]), ds_wgs84.isel(space=[-1])], "space")
```

It is possible to combine heterogeneous geospatial Datasets (e.g., raster,
vector, grid, mesh) as long as they all have a spatial reference coordinate with
the same name and with a `CRSIndex`.

```{code-cell} ipython3
# lat-lon rectilinear grid

ds_grid = xr.Dataset(coords={"lat": np.linspace(-90, 90, 10), "lon": np.linspace(-180, 180, 20)})
ds_grid_wgs84 = ds_grid.proj.assign_crs(spatial_ref="epsg:4326")

# merge the lat-lon grid with the vector data cube
xr.merge([ds_wgs84, ds_grid_wgs84])
```

## Unset the CRS

Just drop the CRS index and/or coordinate

```{code-cell} ipython3
ds_no_crs = ds_wgs84.drop_vars("spatial_ref")

ds_no_crs
```

It is possible to combine datasets with and without a defined CRS. The resulting
dataset will have the common CRS found among all datasets.

```{code-cell} ipython3
ds_wgs84 + ds_no_crs
```
