{{ fullname | escape | underline}}

.. currentmodule:: {{ module }}

.. autoclass:: {{ objname }}

   {% block methods %}

   .. autosummary::
   {% for item in members %}
     {% if item.startswith('_proj') %}
      ~{{ name }}.{{ item }}
     {% endif %}
   {%- endfor %}
   {% endblock %}
