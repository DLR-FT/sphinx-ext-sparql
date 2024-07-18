from __future__ import annotations
from typing import TYPE_CHECKING, ClassVar

from collections.abc import Sequence
from docutils.nodes import paragraph, inline
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective, SphinxRole
from sphinx.locale import __
from pyoxigraph import Store, QuerySolution
from sphinx.domains import Domain
from docutils.parsers.rst.states import Inliner

if TYPE_CHECKING:
    from docutils.nodes import Node, system_message

    from sphinx.application import Sphinx
    from sphinx.util.typing import ExtensionMetadata, OptionSpec


class SparqlAskRole(SphinxRole):
    """Ask a question about the knowledge graph"""

    def run(self) -> tuple[list[Node], list[system_message]]:
        domain = self.env.get_domain("sparql")
        result = domain.ask(self.text)

        print(result)
        if bool(result):
            text = "✓"
        else:
            text = "x"

        return [inline(text=text)], []


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

        domain = self.env.get_domain("sparql")
        # table = paragraph(text="Hello, World!")
        # TODO format into table somehow
        table = []
        for binding in domain.select("\n".join(self.content)):
            text = " | ".join([binding[bound] for bound in bound_vars])
            table += paragraph(text=text)

        return table

class SparqlDomain(Domain):
    """Domain for queryinf the store"""

    name = "sparql"
    label = "SPARQL Domain"
    directives = {"select": SparqlSelectDirective}
    roles = {"ask": SparqlAskRole()}
    store: Store = Store()
    data_version = 0

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
