[![Tests](https://github.com/benbovy/xproj/actions/workflows/test.yml/badge.svg?branch=main&event=push)](https://github.com/benbovy/xproj/actions/workflows/test.yml?query=branch%3Amain+event%3Apush)
[![Docs](https://readthedocs.org/projects/xproj/badge/?version=latest)](https://xproj.readthedocs.io)
[![Coverage](https://codecov.io/gh/benbovy/xproj/branch/main/graph/badge.svg)](https://app.codecov.io/gh/benbovy/xproj?branch=main)

# XProj

A lightweight Xarray extension for managing geospatial coordinate reference
systems (CRS) using PROJ/Pyproj.

*Current development status: experimental, proof-of-concept.*

## Usage

See the [documentation](https://xproj.readthedocs.io).

## Goals

- Provide to Xarray geospatial extensions a set of convenient tools for dealing
  with coordinate reference systems (CRS) in a uniform & flexible way.
- Prevent duplicating CRS-specific logic (e.g., parse, reset, formatting,
  checking equality, etc.) in each extension ; put it together into one reusable
  package instead (i.e., a lightweight Xarray extension mostly built on top of
  [pyproj](https://pyproj4.github.io/pyproj/stable/)).
- Provide a common end-user API for handling CRS via Xarray accessors.
- Leverage recent Xarray features such as custom indexes. Easily compare,
  combine or align Xarray datasets or dataarrays based on their CRS (via
  `CRSIndex`).
- Consolidate the Xarray geospatial ecosystem (towards better interoperability).

## Non-Goals

- Being strongly opinionated on how CRS and other information like spatial
  dimensions should be represented as metadata in Xarray objects and/or in
  Xarray supported I/O formats. This is left to other Xarray extensions and
  format specifications.
- Provide a common set of tools (implementations) for re-projecting data. This
  highly depends on the data type (i.e., raster, vector, etc.) or application
  and it is best handled by other Xarray extensions. We also see XProj
  potentially as a lightweight dependency common to those other extensions so we
  want to restrict XProj's dependencies to the minimum (i.e., Xarray and
  PyProj).
