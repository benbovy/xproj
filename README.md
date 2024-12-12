# XProj

Xarray extension for projections and coordinate reference systems.

**Current development status: experimental, proof-of-concept**

## Usage

See the notebooks in the "examples" folder.

- [Demo](https://nbviewer.org/github/benbovy/xproj/blob/main/examples/demo.ipynb)
- [Interoperability with 3rd-party Xarray extensions](https://nbviewer.org/github/benbovy/xproj/blob/main/examples/xarray_geo_extensions.ipynb)

## Goals

- Provide to Xarray geospatial extensions a set of convenient tools for dealing
  with coordinate reference systems (CRSs) in a uniform & flexible way.
- Prevent duplicating CRS-specific logic (e.g., parse, reset, formatting,
  checking equality, etc.) in each extension ; put it together into one reusable
  package instead (i.e., a lightweight Xarray extension mostly built on top of
  [pyproj](https://pyproj4.github.io/pyproj/stable/)).
- Provide a common end-user API for handling CRS via `.proj` Xarray accessors.
- Leverage recent Xarray features such as custom indexes. Easily compare,
  combine or align Xarray datasets or dataarrays based on their CRS (via
  `CRSIndex`).
- Consolidate the Xarray geospatial ecosystem (towards better interoperability).

## Non-Goals

- Being strongly opinionated on how CRS should be represented as metadata in
  Xarray objects and/or in Xarray supported I/O formats. This is left to other
  Xarray extensions and format specifications (e.g., GeoZarr, GeoTIFF,
  GeoParquet, etc.).
- Provide a common set of tools (implementations) for re-projecting data. This
  highly depends on the data type (i.e., raster, vector, etc.) or application
  and it is best handled by other Xarray extensions.
