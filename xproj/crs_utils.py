from typing import Any

import pyproj


def format_compact_cf(crs: pyproj.CRS) -> dict[str, Any]:
    """Format CRS as a dictionary for minimal compatibility with
    CF conventions.

    More info:
    https://cfconventions.org/cf-conventions/cf-conventions.html

    Parameters
    ----------
    crs : pyproj.crs.CRS
        The input CRS object to format.

    Returns
    -------
    dict
        A dictionary with one ``crs_wkt`` item that contains
        the CRS information formatted as Well-Known Text (WKT).

    See Also
    --------
    xarray.Dataset.proj.write_crs_info
    format_full_cf_gdal

    """
    return {"crs_wkt": crs.to_wkt()}


def format_full_cf_gdal(crs: pyproj.CRS) -> dict[str, Any]:
    """Format CRS as a dictionary for full compatibility with
    CF conventions and GDAL.

    More info:

    - https://cfconventions.org/cf-conventions/cf-conventions.html
    - https://gdal.org/en/stable/drivers/raster/netcdf.html

    Parameters
    ----------
    crs : pyproj.crs.CRS
        The input CRS object to format.

    Returns
    -------
    dict
        A dictionary with two ``crs_wkt`` and ``spatial_ref`` items
        that contains the CRS information formatted as Well-Known Text (WKT),
        as well as items representing all the CF grid mapping variable
        attributes exported via :py:meth:`pyproj.crs.CRS.to_cf`.

    See Also
    --------
    xarray.Dataset.proj.write_crs_info
    format_compact_cf

    """
    output = crs.to_cf()
    output["spatial_ref"] = crs.to_wkt()
    return output
