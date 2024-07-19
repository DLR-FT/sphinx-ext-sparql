from __future__ import annotations
from typing import TYPE_CHECKING

import os

from docutils import nodes
from docutils.parsers.rst import directives
from pathlib import Path
from sphinx.util.docutils import SphinxDirective, SphinxRole
from pyoxigraph import Store, QuerySolution
from sphinx.domains import Domain

if TYPE_CHECKING:
    from docutils.nodes import Node, system_message

    from sphinx.application import Sphinx
    from sphinx.util.typing import ExtensionMetadata


class SparqlAskRole(SphinxRole):
    """Ask a SPARQL question about the knowledge graph"""

    def run(self) -> tuple[list[Node], list[system_message]]:
        rel_filename, filename = self.env.relfn2path(self.text)
        if Path(filename).is_file():
            self.env.note_dependency(rel_filename)
            with open(filename, "r") as f:
                query = f.read()
        else:
            # Assume this is a plain SPARQL query
            query = self.text

        answer = self.ask(query)
        return [answer], []

    def ask(self, query) -> Node:
        domain = self.env.get_domain("sparql")
        result = domain.ask(query)

        if bool(result):
            text = "✓"
        else:
            text = "x"

        return nodes.inline(text=text)


class SparqlSelectDirective(SphinxDirective):
    """Performs a SPARQL query and displays the bound variables as a table"""

    has_content = True
    required_arguments = 0
    option_spec = {
        "bind": directives.unchanged_required,
        "file": directives.unchanged,
    }

    def run(self) -> list(Node):
        if "file" in self.options:
            rel_filename, filename = self.env.relfn2path(self.options["file"])
            self.env.note_dependency(rel_filename)
            with open(filename, "r") as f:
                query = f.read()
        else:
            query = "\n".join(self.content)

        if "bind" in self.options:
            bound_vars = [x.strip() for x in self.options.get("bind").split(",")]
        else:
            bound_vars = []

        table = self.table(bound_vars, query)

        return [table]

    def table(self, bound_vars, query) -> nodes.table:
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

        return table


class SparqlDomain(Domain):
    """Domain for queryinf the store"""

    name = "sparql"
    label = "SPARQL Domain"
    directives = {"select": SparqlSelectDirective}
    roles = {"ask": SparqlAskRole()}
    data_version = 0

    @property
    def store(self) -> Store:
        return Store(path=self.env.sparql_store_path)

    def ask(self, query: str) -> bool:
        return self.store.query(query)

    def select(self, query: str) -> QuerySolution:
        for solution in self.store.query(query):
            yield solution


def load_store(app, env, docnames):
    env.sparql_store_path = os.path.join(app.outdir, "db")
    store: Store = Store(path=env.sparql_store_path)
    store.clear()

    for input, mime in app.config["sparql_load"]:
        path = os.path.join(app.srcdir, input)
        store.load(path, mime)

    store.flush()


def setup(app: Sphinx) -> ExtensionMetadata:
    app.add_config_value("sparql_load", default=[], rebuild="html")
    app.add_domain(SparqlDomain)
    app.connect("env-before-read-docs", load_store)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
    }
