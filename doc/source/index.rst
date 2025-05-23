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

    select ?Subject ?p ?Object { ?sub ?p ?obj }

This renders to

.. sparql:select::
  :file: list_sub_obj.rq

The following directive is equivalent but gets the query from a file in `srcdir`.

.. code-block:: rst

  .. sparql:select::
      :file: list_sub_obj.rq
      :bind: Subject, Object

The same data can be displayed as a cross product table (also known as pivot table).

.. code-block:: rst

  .. sparql::select_cross
      :file: list_titles.rq
      :dimension-x: Object
      :dimension-y: Subject

This renders to this table:

.. sparql:select-cross::
  :file: list_titles.rq
  :dimension-x: Object
  :dimension-y: Subject


Rules
-----

Questions about the knowledge graph can be asked using `sparql:ask` which either takes the verbatim query as its argument or a path inside :code:`srcdir` that contains a query.

.. code-block:: rst

  Is the SPARQL tutorial mentioned in the knowledge graph? :sparql:ask:`ask { ?s ?p "SPARQL Tutorial" }`

Renders to

Is the SPARQL tutorial mentioned in the knowledge graph? :sparql:ask:`ask { ?s ?p "SPARQL Tutorial" }`
