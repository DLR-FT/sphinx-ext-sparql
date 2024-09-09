from __future__ import annotations
from typing import TYPE_CHECKING, Union

from collections import defaultdict
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

    def table(self, query, bound_vars: Union[None, list[str]] = None) -> nodes.table:
        domain = self.env.get_domain("sparql")
        if isinstance(domain, SparqlDomain):
            results = domain.select(query)
        else:
            raise SparqlExtError("SPARQL domain not initialized")

        return render_table(results, bound_vars)


class SparqlSelectCrosstabDirective(SphinxDirective):
    """Performs a SPARQL query and displays the bound variables as a cross product table"""

    has_content = True
    required_arguments = 0
    option_spec = {
        "dimension-x": directives.unchanged_required,
        "dimension-y": directives.unchanged_required,
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

        try:
            table = self.table(
                query, self.options["dimension-x"], self.options["dimension-y"]
            )
            return [table]
        except SparqlExtError as e:
            logger.error(f"[sparql_sphinx] {e}")
            return []

    def table(self, query, dimension_x, dimension_y) -> nodes.table:
        domain = self.env.get_domain("sparql")
        if isinstance(domain, SparqlDomain):
            results = domain.select(query)
        else:
            raise SparqlExtError("SPARQL domain not initialized")

        return render_crosstab(results, dimension_x, dimension_y)


def render_crosstab(results: QuerySolutions, dimension_x, dimension_y) -> nodes.table:
    table = nodes.table()
    table["classes"] += ["colwidths-auto"]

    matrix = defaultdict(dict)

    variables = [x.value for x in results.variables]

    if dimension_x not in variables:
        logger.error(f'[sphinx_sparql]: Binding "{dimension_x}" not provided in query')
        return table

    if dimension_y not in variables:
        logger.error(f'[sphinx_sparql]: Binding "{dimension_y}" not provided in query')
        return table

    for res in results:
        x = res[dimension_x].value
        y = res[dimension_y].value
        matrix[y][x] = "✓"

    def dimension_x_labels(matrix):
        return set([item for row in matrix for item in list(matrix[row])])

    def dimension_y_labels(matrix):
        return set([row for row in matrix])

    dimension_x_labels = dimension_x_labels(matrix)
    dimension_y_labels = dimension_y_labels(matrix)

    tgroup = nodes.tgroup(cols=len(dimension_x_labels) + 1)

    # Add columns for each possible variable of dimension_x and the column for the variable of dimension_y
    for i in range(0, len(dimension_x_labels) + 1):
        colspec = nodes.colspec()
        tgroup += colspec

    table += tgroup

    table_rows = []
    for y_label in dimension_y_labels:
        table_row_node = nodes.row()

        def y_label_node(row):
            y_label = nodes.entry()
            y_label += nodes.paragraph(text=row)
            return y_label

        table_row_node += y_label_node(y_label)

        for x_label in dimension_x_labels:
            table_entry = nodes.entry()
            value = matrix.get(y_label, dict()).get(x_label, "")
            table_entry += nodes.paragraph(text=value)
            table_row_node += table_entry

        table_rows.append(table_row_node)

    thead = nodes.thead()

    table_hrow = nodes.row()

    def y_column_title():
        table_y_label_entry = nodes.entry()
        table_y_label_entry += nodes.paragraph(text="")
        return table_y_label_entry

    table_hrow += y_column_title()

    for var in dimension_x_labels:
        entry = nodes.entry()
        entry += nodes.paragraph(text=var)
        table_hrow += entry

    thead.extend([table_hrow])
    tgroup += thead

    tbody = nodes.tbody()
    tbody.extend(table_rows)
    tgroup += tbody

    return table


def render_table(results, bound_vars=None) -> nodes.table:
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
                logger.error(f'[sphinx_sparql]: Binding "{var}" not provided in query')
                continue
            named_node = binding[var]
            value = getattr(named_node, "value", None)
            entry += nodes.paragraph(text=value)
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
    directives = {
        "select": SparqlSelectDirective,
        "select-cross": SparqlSelectCrosstabDirective,
    }
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
