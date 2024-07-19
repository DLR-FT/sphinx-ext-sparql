.. include:: ../../README.rst

Configuration
-------

``sparql_load``
  * type:  list(tuple(str, str))
  * default: []

List of files to load into the knowledge graph as a list of tuples of file names in :code:`srcdir` and their MIME types (e.g. `text/turtle`).

Directives
----------

.. code-block:: rst

  .. sparql:select::
    :file: list_sub_obj.rq
    :bind: sub, obj

    select ?sub ?p ?obj { ?sub ?p ?obj }

This renders to

.. sparql:select::
  :file: list_sub_obj.rq
  :bind: sub, obj

The following directive is equivalent but gets the query from a file in `srcdir`.

.. code-block:: rst

  .. sparql:select::
      :file: list_sub_obj.rq
      :bind: sub, obj

Rules
-----

Questions about the knowledge graph can be asked using `sparql:ask` which either takes the verbatim query as its argument or a path inside :code:`srcdir` that contains a query.

.. code-block:: rst

  Is the SPARQL tutorial mentioned in the knowledge graph? :sparql:ask:`ask { ?s ?p "SPARQL Tutorial" }`

Renders to

Is the SPARQL tutorial mentioned in the knowledge graph? :sparql:ask:`ask { ?s ?p "SPARQL Tutorial" }`
