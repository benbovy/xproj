.. _api:

API Reference
=============

.. currentmodule:: xarray

Dataset ``proj`` extension
--------------------------

CRS properties

.. autosummary::
   :toctree: _api_generated/
   :template: autosummary/accessor_attribute.rst

   Dataset.proj.crs_indexes
   Dataset.proj.crs_aware_indexes
   Dataset.proj.crs

CRS methods

.. autosummary::
   :toctree: _api_generated/
   :template: autosummary/accessor_method.rst

   Dataset.proj.assign_crs
   Dataset.proj.map_crs


DataArray ``proj`` extension
----------------------------

CRS properties

.. autosummary::
   :toctree: _api_generated/
   :template: autosummary/accessor_attribute.rst

   DataArray.proj.crs_indexes
   DataArray.proj.crs_aware_indexes
   DataArray.proj.crs

CRS methods

.. autosummary::
   :toctree: _api_generated/
   :template: autosummary/accessor_method.rst

   DataArray.proj.assign_crs
   DataArray.proj.map_crs

.. currentmodule:: xproj

3rd-party Xarray extensions
---------------------------

.. autosummary::
   :toctree: _api_generated/

   ProjAccessorMixin
   ProjIndexMixin
   register_accessor
