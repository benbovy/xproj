{{ fullname | escape | underline}}

.. currentmodule:: {{ module }}

.. autoclass:: {{ objname }}

   {% block methods %}
   .. automethod:: __init__
   {% endblock %}

   {% block attributes %}
   .. rubric:: {{ _('Attributes') }}

   .. autosummary::
      ~CRSIndex.crs
   {% endblock %}
