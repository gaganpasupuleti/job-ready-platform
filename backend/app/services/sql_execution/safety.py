"""AST-based SQL safety validation using sqlglot (PostgreSQL dialect).

Application parsing is the first layer. Database permissions and read-only
transactions remain the final security boundary.
"""

from __future__ import annotations

import re

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

# Statement / node types that are never allowed in student SQL
_FORBIDDEN_TYPE_NAMES = (
    "Insert",
    "Update",
    "Delete",
    "Merge",
    "Drop",
    "Create",
    "Copy",
    "TruncateTable",
    "Grant",
    "Revoke",
    "Command",
    "Set",
    "Use",
    "Transaction",
    "Commit",
    "Rollback",
    "Kill",
    "Analyze",
    "AlterColumn",
    "AlterTable",
    "AddConstraint",
    "DropPartition",
    "RenameColumn",
    "RenameTable",
    "Replace",
    "Pragma",
    "Refresh",
    "Execute",
    "Prepare",
    "Deallocate",
    "Lock",
    "Unlock",
    "Attach",
    "Detach",
)

FORBIDDEN_NODE_TYPES: tuple[type, ...] = tuple(
    cls
    for name in _FORBIDDEN_TYPE_NAMES
    if (cls := getattr(exp, name, None)) is not None
)

# Tables that must not be queried for reconnaissance
FORBIDDEN_TABLE_NAMES = frozenset(
    {
        "pg_roles",
        "pg_user",
        "pg_shadow",
        "pg_authid",
        "pg_auth_members",
        "pg_database",
        "pg_settings",
        "pg_stat_activity",
        "pg_stat_database",
        "pg_stat_statements",
        "pg_file_settings",
        "pg_hba_file_rules",
        "pg_config",
        "pg_tablespace",
        "pg_user_mappings",
        "pg_foreign_servers",
        "pg_foreign_tables",
    }
)

# Dangerous functions (file / admin / network / config)
FORBIDDEN_FUNCTIONS = frozenset(
    {
        "pg_read_file",
        "pg_read_binary_file",
        "pg_write_file",
        "pg_ls_dir",
        "pg_stat_file",
        "lo_import",
        "lo_export",
        "lo_get",
        "lo_put",
        "lo_from_bytea",
        "lo_unlink",
        "dblink",
        "dblink_exec",
        "dblink_connect",
        "dblink_connect_u",
        "current_setting",
        "set_config",
        "pg_sleep",
        "pg_terminate_backend",
        "pg_cancel_backend",
        "pg_reload_conf",
        "pg_rotate_logfile",
        "inet_server_addr",
        "inet_server_port",
        "inet_client_addr",
        "inet_client_port",
        "pg_backend_pid",
        "pg_create_logical_replication_slot",
        "pg_drop_replication_slot",
        "query_to_xml",
        "database_to_xml",
    }
)


def _table_parts(table: exp.Table) -> tuple[str | None, str]:
    catalog = table.catalog.lower() if table.catalog else None
    db = table.db.lower() if table.db else None
    name = table.name.lower() if table.name else ""
    schema = db or catalog
    return schema, name


def _function_name(node: exp.Expression) -> str | None:
    if isinstance(node, exp.Anonymous):
        return str(node.this).lower() if node.this else None
    if isinstance(node, exp.Func):
        sql_name = getattr(node, "sql_name", None)
        if callable(sql_name):
            try:
                return str(sql_name()).lower()
            except Exception:
                pass
        return type(node).__name__.lower()
    return None


def validate_sql_query(query: str, *, max_length: int = 20000) -> str | None:
    """Return an error message if unsafe, else None.

    Uses sqlglot PostgreSQL AST parsing. Rejects mutation/DDL anywhere in the
    tree (including modifying CTEs), multi-statement batches, restricted
    catalogs, and dangerous functions.
    """
    if not query or not query.strip():
        return "Query cannot be empty."
    if len(query) > max_length:
        return f"Query exceeds maximum length of {max_length} characters."

    try:
        trees = sqlglot.parse(query, read="postgres")
    except ParseError:
        return "Query could not be parsed as valid PostgreSQL SQL."
    except Exception:
        return "Query could not be parsed as valid PostgreSQL SQL."

    statements = [t for t in trees if t is not None]
    if not statements:
        return "Query cannot be empty."
    if len(statements) > 1:
        return "Multiple SQL statements are not allowed."

    root = statements[0]

    if not isinstance(root, exp.Select):
        return "Only a single read-only SELECT (or WITH ... SELECT) query is allowed."

    for node in root.walk():
        for forbidden in FORBIDDEN_NODE_TYPES:
            if isinstance(node, forbidden):
                label = type(node).__name__.upper()
                if isinstance(node, exp.Command):
                    return "Unsupported or privileged SQL command is not allowed."
                if type(node).__name__ in {"Delete", "Insert", "Update", "Merge"}:
                    return (
                        f"Data-modifying statement '{label}' is not allowed "
                        "(including inside CTEs)."
                    )
                return f"Statement type '{label}' is not allowed."

        if isinstance(node, exp.Table):
            schema, name = _table_parts(node)
            if name in FORBIDDEN_TABLE_NAMES:
                return "Query references restricted system catalogs or schemas."
            if schema:
                return "Schema-qualified table references are not allowed."

        fn = _function_name(node)
        if fn and fn in FORBIDDEN_FUNCTIONS:
            return f"Function '{fn}' is not allowed."

    upper_compact = re.sub(r"\s+", " ", query.upper())
    if "SET SEARCH_PATH" in upper_compact or "SET ROLE" in upper_compact:
        return "Changing session configuration is not allowed."
    if "SET SESSION" in upper_compact or "SET LOCAL" in upper_compact:
        return "Changing session configuration is not allowed."

    return None
