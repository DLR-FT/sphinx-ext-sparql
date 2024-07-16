from __future__ import annotations
from typing import TYPE_CHECKING, ClassVar

from sphinx import addnodes as sphinxnodes  # noqa: F401
from sphinx.util.docutils import SphinxDirective
from sphinx.locale import __

if TYPE_CHECKING:
    from docutils.nodes import Node

    from sphinx.application import Sphinx
    from sphinx.util.typing import ExtensionMetadata, OptionSpec


class SparqlQueryDirective(SphinxDirective):
    has_content = True
    requires_arguments = 0
    optional_arguments = 1
    option_spec: ClassVar[OptionSpec] = { }

    def run(self) -> list[Node]:
        if self.arguments:
            document = self.state.document
            return [document.reporter.warning(
                __("SPARQL extension cannot have a filename argument"), line=self.lineno
            )]

        # Join all lines to query
        sparql_query = "\n".join(self.content)
        if not sparql_query.strip():
            return [self.state_machine.reporter.warning(__("Ignoring sparql_query directive without content.", line=self.lineno))]
        text = "TODO run query"

        return [text]
            

def setup(app: Sphinx) -> ExtensionMetadata:
    app.add_directive("sparql", SparqlQueryDirective)
    app.add_config_value("sparql_store", default = None)
    return {
        "version": "0",
        "parallel_read_safe": True,
    }
