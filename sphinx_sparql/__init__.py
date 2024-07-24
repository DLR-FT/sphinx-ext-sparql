from __future__ import annotations
from typing import TYPE_CHECKING, Union

from docutils import nodes
from docutils.parsers.rst import directives
from os import path
from pathlib import Path
from sphinx.environment import BuildEnvironment
from sphinx.errors import SphinxError
from sphinx.util.docutils import SphinxDirective, SphinxRole
from pyoxigraph import Store, QuerySolutions
from sphinx.domains import Domain
from sphinx.util import logging

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from docutils.nodes import Node, system_message

    from sphinx.application import Sphinx
    from sphinx.util.typing import ExtensionMetadata


class SparqlExtError(SphinxError):
    category = "Sparql extension error"


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

        try:
            answer = self.ask(query)
            return [answer], []
        except SparqlExtError as e:
            return [], [e]


    def ask(self, query) -> Node:
        domain = self.env.get_domain("sparql")
        if isinstance(domain, SparqlDomain):
            result = domain.ask(query)
        else:
            logger.error("[sphinx_sparql]: SPARQL domain not initialized")

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

    def run(self) -> list[Node]:
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
            bound_vars = None

        try:
            table = self.table(query, bound_vars)
            return [table]
        except SparqlExtError as e:
            logger.error(f"[sparql_sphinx] {e}")
            return []


    def table(self, query, bound_vars: Union[None, list[str]]=None) -> nodes.table:
        domain = self.env.get_domain("sparql")
        if isinstance(domain, SparqlDomain):
            results = domain.select(query)
        else:
            raise SparqlExtError("SPARQL domain not initialized")

        return render_table(self, results, bound_vars)



def render_table(self, results, bound_vars=None) -> nodes.table:
    if bound_vars is None:
        bound_vars = [var.value for var in results.variables]

    table = nodes.table()
    table["classes"] += ["colwidths-auto"]
    tgroup = nodes.tgroup(cols=len(bound_vars))

    for var in bound_vars:
        colspec = nodes.colspec()
        tgroup += colspec

    table += tgroup

    rows = []
    for binding in results:
        row_node = nodes.row()
        for var in bound_vars:
            entry = nodes.entry()
            if var not in [var.value for var in results.variables]:
                logger.error(f"[sphinx_sparql]: Binding \"{var}\" not provided in query")
                continue
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
        return Store.read_only(path.join(self.env.app.outdir, "db"))

    def ask(self, query: str) -> bool:
        try:
            return self.store.query(query)
        except (SyntaxError, IOError) as e:
            raise SparqlExtError(f"{e}")

    def select(self, query: str) -> QuerySolutions:
        try:
            results = self.store.query(query)
        except (SyntaxError, IOError) as e:
            raise SparqlExtError(f"{e}")

        return results


def load_store(app: Sphinx, env: BuildEnvironment, docnames: list[str]):
    sparql_store_path = path.join(app.outdir, "db")
    store: Store = Store(path=sparql_store_path)
    store.clear()

    for input, mime in app.config["sparql_load"]:
        if not path.isabs(input):
            input = path.join(app.srcdir, input)
        try:
            store.bulk_load(input, mime)
        except ValueError:
            raise SparqlExtError(f"Unsupported MIME type {mime} for input file {input}")
        except SyntaxError as e:
            raise SparqlExtError(f"Invalid syntax input file {input}: {e.text}")

    store.flush()


def setup(app: Sphinx) -> ExtensionMetadata:
    app.add_config_value("sparql_load", default=[], rebuild="html")
    app.add_domain(SparqlDomain)
    app.connect("env-before-read-docs", load_store)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
    }
