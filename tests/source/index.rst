* Is the SPARQL tutorial mentioned in the knowledge graph? :sparql:ask:`ask { ?s ?p "SPARQL Tutorial" }`
* Is the SPARQL tutorial mentioned in the knowledge graph (but query is read from file)? :sparql:ask:`ask_tutorial.rq`

List subjects and objects using query stored in file
====================================================

.. sparql:select::
    :file: list_sub_obj.rq
    :bind: sub, obj

List subjects and objects using plain query
===========================================

.. sparql:select::
    :file: list_sub_obj.rq
    :bind: sub, obj

    select ?sub ?p ?obj {
      ?sub ?p ?obj
    }
