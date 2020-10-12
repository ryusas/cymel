class {{ fullname }}
======{{ underline }}

.. currentmodule:: {{ module }}
{#
.. currentmodule:: {{ fullname|owner_module }}
#}

.. inheritance-diagram:: {{ objname }}
    :parts: 1

{#
.. autoclass:: {{ objname }}
    :show-inheritance:
    :members:
    :undoc-members:
#}

.. autoclass:: {{ objname }}
    :show-inheritance:

{% block methods_summary %}
{% if methods|in_class(module,objname) %}
    .. rubric:: Methods:

    .. autosummary::
    {% for item in methods|in_class(module,objname) %}
        {{ item }}
    {%- endfor %}
{% endif %}
{% endblock %}

{% block attributes %}
{% if attributes|in_class(module,objname) %}
    .. rubric:: Attributes:

    {% for item in attributes|in_class(module,objname) %}
    .. autoattribute:: {{ item }}
    {%- endfor %}
{% endif %}
{% endblock %}

{% block methods %}
{% if methods|in_class(module,objname) %}
    .. rubric:: Methods Details:

    {% for item in methods|in_class(module,objname) %}
    .. automethod:: {{ item }}
    {%- endfor %}
{% endif %}
{% endblock %}

