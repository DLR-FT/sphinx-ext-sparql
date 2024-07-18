from __future__ import annotations
from typing import TYPE_CHECKING

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective, SphinxRole
from pyoxigraph import Store, QuerySolution
from sphinx.domains import Domain

if TYPE_CHECKING:
    from docutils.nodes import Node, system_message

    from sphinx.application import Sphinx
    from sphinx.util.typing import ExtensionMetadata


class SparqlAskRole(SphinxRole):
    """Ask a question about the knowledge graph"""

    def run(self) -> tuple[list[Node], list[system_message]]:
        domain = self.env.get_domain("sparql")
        result = domain.ask(self.text)

        if bool(result):
            text = "✓"
        else:
            text = "x"

        return [nodes.inline(text=text)], []


class SparqlSelectDirective(SphinxDirective):
    """Performs a SPARQL query and displays the bound variables as a table"""

    has_content = True
    required_arguments = 0
    option_spec = {
        "bind": directives.unchanged_required,
    }

    def run(self) -> list(Node):
        if "bind" in self.options:
            bound_vars = [x.strip() for x in self.options.get("bind").split(",")]
        else:
            bound_vars = []

        query = "\n".join(self.content)

        table = nodes.table()
        table["classes"] += ["colwidths-auto"]
        tgroup = nodes.tgroup(cols=len(bound_vars))

        for var in bound_vars:
            colspec = nodes.colspec()
            tgroup += colspec

        table += tgroup

        rows = []
        for binding in self.env.get_domain("sparql").select(query):
            row_node = nodes.row()
            for var in bound_vars:
                entry = nodes.entry()
                named_node = binding[var]
                entry += nodes.paragraph(text=named_node.value)
                row_node += entry
            rows.append(row_node)


        thead = nodes.thead()

        hrow = nodes.row()
        for var in bound_vars:
            entry = nodes.entry()
            entry += nodes.paragraph(text=var)
            hrow += entry

        thead.extend([hrow])
        tgroup += thead

        tbody = nodes.tbody()
        tbody.extend(rows)
        tgroup += tbody
        breakpoint()

        return [table]

class SparqlDomain(Domain):
    """Domain for queryinf the store"""

    name = "sparql"
    label = "SPARQL Domain"
    directives = {"select": SparqlSelectDirective}
    roles = {"ask": SparqlAskRole()}
    data_version = 0

    @property
    def store(self) -> Store:
        return Store(path=self.env.config["sparql_store"])

    def ask(self, query: str) -> bool:
        return  self.store.query(query)

    def select(self, query: str) -> QuerySolution:
        for solution in self.store.query(query):
            yield solution

def setup(app: Sphinx) -> ExtensionMetadata:
    # TODO multiple directives, bindings as args etc? What is the interface to use the bindings in the document? Table?
    app.add_config_value("sparql_store", default=None, rebuild="html")
    app.add_domain(SparqlDomain)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
    }
