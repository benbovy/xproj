# XProj Documentation

A lightweight Xarray extension for managing geospatial coordinate reference
systems (CRS) using PROJ/[Pyproj].

**Useful links**:
[Home](http://xproj.readthedocs.io/) |
[Code Repository](https://github.com/benbovy/xproj) |
[Issues](https://github.com/benbovy/xproj/issues) |
[Discussions](https://github.com/benbovy/xproj/discussions) |
[Releases](https://github.com/benbovy/xproj/releases)

## Contents

```{toctree}
:maxdepth: 1

install
usage
integration
api
```

## Motivation

### Goals

- Provide to Xarray geospatial extensions a set of convenient tools for dealing
  with coordinate reference systems (CRSs) in a uniform & flexible way.
- Prevent duplicating CRS-specific logic (e.g., parse, reset, formatting,
  checking equality, etc.) in each extension ; put it together into one reusable
  package instead (i.e., a lightweight Xarray extension mostly built on top of
  [Pyproj]).
- Provide a common end-user API for handling CRS via `.proj` Xarray accessors.
- Leverage recent Xarray features such as custom indexes. Easily compare,
  combine or align Xarray datasets or dataarrays based on their CRS (via
  `CRSIndex`).
- Consolidate the Xarray geospatial ecosystem (towards better interoperability).

### Non-Goals

- Being strongly opinionated on how CRS and other information like spatial
  dimensions should be represented as metadata in Xarray objects and/or in
  Xarray supported I/O formats. This is left to other Xarray extensions and
  format specifications (e.g., GeoZarr, GeoTIFF, GeoParquet, etc.).
- Provide a common set of tools (implementations) for re-projecting data. This
  highly depends on the data type (i.e., raster, vector, etc.) or application
  and it is best handled by other Xarray extensions. We also see XProj
  potentially as a lightweight dependency common to those other extensions so we
  want to restrict XProj's dependencies to the minimum (i.e., Xarray and
  PyProj).

[Pyproj]: https://pyproj4.github.io/pyproj/stable/
