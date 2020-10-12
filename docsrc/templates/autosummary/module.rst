{{ fullname }}
{{ underline }}

.. automodule:: {{ fullname }}

{% block classes_summary %}
{% if classes|in_module(fullname) %}
    .. rubric:: Classes:

    .. autosummary::
        :toctree: classes
        :nosignatures:
    {% for item in classes|in_module(fullname) %}
        {{ item }}
    {%- endfor %}
{% endif %}
{% endblock %}

{% block exceptions_summary %}
{% if exceptions|in_module(fullname) %}
    .. rubric:: Exceptions:

    .. autosummary::
    {% for item in exceptions|in_module(fullname) %}
        {{ item }}
    {%- endfor %}
{% endif %}
{% endblock %}

{% block functions_summary %}
{% if functions|in_module(fullname) %}
    .. rubric:: Functions:

    .. autosummary::
    {% for item in functions|in_module(fullname) %}
        {{ item }}
    {%- endfor %}
{% endif %}
{% endblock %}



{% block aliases %}
{% if (classes+exceptions+functions)|if_alias(fullname) %}
    .. rubric:: Aliases:

    {% for item in (classes+exceptions+functions)|if_alias(fullname) %}
    .. autodata:: {{ item }}
    {%- endfor %}
{% endif %}
{% endblock %}

{% block costants %}
{% if members|in_module(fullname)|if_constant(fullname) %}
    .. rubric:: Constants:

    {% for item in members|in_module(fullname)|if_constant(fullname) %}
    .. autodata:: {{ item }}
    {%- endfor %}
{% endif %}
{% endblock %}

{% block exceptions %}
{% if exceptions|in_module(fullname) %}
    .. rubric:: Exceptions Details:

    {% for item in exceptions|in_module(fullname) %}
    .. autoexception:: {{ item }}
    {%- endfor %}
{% endif %}
{% endblock %}

{% block functions %}
{% if functions|in_module(fullname) %}
    .. rubric:: Functions Details:

    {% for item in functions|in_module(fullname) %}
    .. autofunction:: {{ item }}
    {%- endfor %}
{% endif %}
{% endblock %}

