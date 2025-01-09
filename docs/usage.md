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
mystnb:
  render_error_lexer: none
---

# Usage Examples

```{code-cell} ipython3
import numpy as np
import pyproj
import xarray as xr
import xproj

xr.set_options(display_expand_indexes=True);
```

## Example dataset

We'll use an Xarray tutorial dataset as example.

```{code-cell} ipython3
ds = xr.tutorial.load_dataset("air_temperature")

ds
```

This example dataset has no explicit coordinate reference system ({term}`CRS`)
specified. It represents a subset of [reanalysis
data](https://psl.noaa.gov/data/gridded/data.ncep.reanalysis.html) on a global
latitude-longitude (gaussian) grid.

## Setting the CRS

Using the dataset loaded above in GIS applications may require setting a CRS
first.

This can be done using {meth}`xarray.Dataset.proj.assign_crs` that creates a new
{term}`spatial reference coordinate` (if it doesn't exist yet), i.e., a scalar
coordinate with a {class}`~xproj.CRSIndex`.

Here we specify the common WGS84 global geodetic CRS ([EPSG code:
4326](https://epsg.io/4326)).

:::{note}
The name of the spatial reference coordinate is arbitrary. ``spatial_ref`` is
chosen here as it is a common name (it is used by default in
[rioxarray](https://corteva.github.io/rioxarray) and
[odc-geo](https://odc-geo.readthedocs.io)).
:::

```{code-cell} ipython3
ds_wgs84 = ds.proj.assign_crs(spatial_ref="epsg:4326")

ds_wgs84
```

## Getting the CRS

The easiest way to access the CRS is via the {attr}`xarray.Dataset.proj.crs`
property, which returns a
[pyproj.CRS](https://pyproj4.github.io/pyproj/stable/api/crs/crs.html) object.

```{code-cell} ipython3
ds_wgs84.proj.crs
```

Alternatively, it is possible to explicitly pass the name of the {term}`spatial
reference coordinate` to the `.proj` accessor:

```{code-cell} ipython3
ds_wgs84.proj("spatial_ref").crs
```

## Writing CRS information

Before saving the dataset to a given format, it may be useful to write the CRS
information as coordinate metadata (attributes) so it could be later loaded by
other tools like GDAL that understand this metadata. This can be done with
{meth}`xarray.Dataset.proj.write_crs_info`:

```{code-cell}
ds_info = ds_wgs84.proj.write_crs_info()

ds_info.spatial_ref
```

Conversely, the attributes of the spatial reference coordinates can be cleared
via {meth}`xarray.Dataset.proj.clear_crs_info`.

## CRS-aware alignment

One of the main motivations of associating a {class}`~xproj.CRSIndex` with a
{term}`spatial reference coordinate` is to compare or align xarray objects based
on their {term}`CRS`.

To illustrate how it works, let's clone the example dataset and assume that the
latitude and longitude coordinate values are relative to the WGS72 CRS ([EPSG
code: 4322](https://epsg.io/4322)):

```{code-cell} ipython3
ds_wgs72 = ds_wgs84.proj.assign_crs(spatial_ref="epsg:4322", allow_override=True)
```

Note the nice error message below when trying to combine the two datasets with
different CRS (only works if the spatial reference coordinates have the same
name). The error is raised by Xarray itself and shows the {func}`repr` of the
respective ``CRSIndex`` objects as detailed information.

```{code-cell} ipython3
:tags: [raises-exception]

ds_wgs84 + ds_wgs72
```

Since it relies on Xarray indexes, CRS-based auto-alignment also works
seamlessly for many operations such as {func}`xarray.concat`:

```{code-cell} ipython3
xr.concat([ds_wgs84.isel(lat=[0, 1]), ds_wgs84.isel(lat=[-1])], "lat")
```

It is also possible to combine heterogeneous geospatial Datasets (e.g., raster,
vector, grid, mesh) as long as they all have an indexed {term}`spatial reference
coordinate` with the same name:

```{code-cell} ipython3
# lat-lon trajectory
ds_traj = xr.Dataset(
    coords={
        "latitude": ("traj", [73, 80, 76]),
        "longitude": ("traj", [220, 260, 270]),
    },
)
ds_traj_wgs84 = ds_traj.proj.assign_crs(spatial_ref="epsg:4326")

# merge the lat-lon grid with the vector data cube
xr.merge([ds_wgs84, ds_traj_wgs84])
```

## Clearing the CRS

Just drop the {term}`spatial reference coordinate`:

```{code-cell} ipython3
ds_no_crs = ds_wgs84.drop_vars("spatial_ref")

ds_no_crs
```

Note that it is possible to combine datasets with and without a defined CRS. The
resulting dataset will have the common CRS found among all datasets.

```{code-cell} ipython3
ds_wgs84 + ds_no_crs
```

## Multi-CRS Dataset or DataArray

Xproj supports Dataset or DataArray objects with multiple {term}`spatial
reference coordinates <spatial reference coordinate>`.

:::{warning}
This feature is experimental and may be removed in the future.
:::

One possible use case is having a dataset with both geographic and projected
coordinates, e.g.,

```{code-cell} ipython3
projected_crs = pyproj.CRS.from_epsg(4087)

p = pyproj.Proj(projected_crs)
lonlon, latlat = np.meshgrid(ds.lon, ds.lat)
xx, yy = p(lonlon - 360, latlat)

ds_both = (
    ds_wgs84
    .rename_vars(spatial_ref="geographic_ref")
    .assign_coords(x=(("lat", "lon"), xx), y=(("lat", "lon"), yy))
    .proj.assign_crs(projected_ref=projected_crs)
)

ds_both
```

Trying to access the (unique) CRS of the dataset raises an error:

```{code-cell} ipython3
:tags: [raises-exception]

ds_both.proj.crs
```

To access either the geographic or the projected CRS, the name of the
corresponding spatial reference coordinate must be passed explicitly to the
`.proj` accessor:

```{code-cell} ipython3
ds_both.proj("projected_ref").crs
```
