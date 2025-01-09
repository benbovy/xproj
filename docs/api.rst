.. _api:

API Reference
=============

.. currentmodule:: xarray

.. _proj_accessors:

Dataset ``proj`` extension
--------------------------

XProj extends :py:class:`xarray.Dataset` with the properties and methods below.
To enable it, be sure to import ``xproj`` after ``xarray``:

.. code-block:: python

   >>> import xarray as xr
   >>> import xproj

**CRS properties**

.. autosummary::
   :toctree: _api_generated/
   :template: autosummary/accessor_attribute.rst

   Dataset.proj.crs_indexes
   Dataset.proj.crs_aware_indexes
   Dataset.proj.crs

**CRS methods**

.. autosummary::
   :toctree: _api_generated/
   :template: autosummary/accessor_method.rst

   Dataset.proj.assign_crs
   Dataset.proj.map_crs
   Dataset.proj.write_crs_info
   Dataset.proj.clear_crs_info


DataArray ``proj`` extension
----------------------------

XProj extends :py:class:`xarray.DataArray` with the properties and methods below.
To enable it, be sure to import ``xproj`` after ``xarray``:

.. code-block:: python

   >>> import xarray as xr
   >>> import xproj

**CRS properties**

.. autosummary::
   :toctree: _api_generated/
   :template: autosummary/accessor_attribute.rst

   DataArray.proj.crs_indexes
   DataArray.proj.crs_aware_indexes
   DataArray.proj.crs

**CRS methods**

.. autosummary::
   :toctree: _api_generated/
   :template: autosummary/accessor_method.rst

   DataArray.proj.assign_crs
   DataArray.proj.map_crs
   DataArray.proj.write_crs_info
   DataArray.proj.clear_crs_info

.. currentmodule:: xproj

3rd-party Xarray extensions
---------------------------

XProj provides some utilities (Mixin classes, decorators) for easier integration
with 3rd-party Xarray geospatial extensions.

.. autosummary::
   :toctree: _api_generated/
   :template: autosummary/mixin.rst

   ProjAccessorMixin
   ProjIndexMixin

.. autosummary::
   :toctree: _api_generated/

   register_accessor
