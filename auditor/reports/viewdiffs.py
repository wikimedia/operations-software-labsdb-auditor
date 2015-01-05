# Copyright 2015 Yuvi Panda <yuvipanda@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import re
import logging
from pyparsing import OneOrMore, Optional, Word, SkipTo, StringEnd, alphanums

from ..models import Column, Table
from ..utils import get_tables, diff_iters, common_iters


def _diff(expected, actual, fields):
    diff = {}
    for field in fields:
        a = expected.__getattribute__(field)
        b = actual.__getattribute__(field)
        if a != b:
            diff[field] = {
                'expected': a,
                'found': b
            }
    return diff


def diff_columns(expected, actual):
    return _diff(expected, actual, ('name', 'whitelisted', 'condition', 'replacewith'))


def diff_tables(expected, actual):
    table_diff = _diff(expected, actual, ('name', 'where', 'table_name'))
    missing_cols, extra_cols = diff_iters(expected.columns, actual.columns)
    common_columns = common_iters(actual.columns, expected.columns)
    column_diffs = {}
    for name in common_columns:
        col_diff = diff_columns(expected.columns[name], actual.columns[name])
        if col_diff:
            column_diffs[name] = col_diff

    column_info = {}
    if missing_cols:
        column_info['missing'] = missing_cols
    if extra_cols:
        column_info['extra'] = extra_cols
    if column_diffs:
        column_info['diff'] = column_diffs
    if column_info:
        table_diff['columns'] = column_info
    return table_diff if table_diff else None


EXTRACT_VIEWDEF_RE = re.compile(r"DEFINER VIEW `([^`]+)` AS (.*)")


def _cleanup_viewdefiner(full_sql, db, table):
    """
    Clean up the view definer SQL to make it easier to parse

    Picks out only the SELECT statement from the definer.
    Also reduces all references of form dbname.tablename.column to just column
    Removes backticks as well
    """
    definer_sql = EXTRACT_VIEWDEF_RE.search(full_sql).groups()[1]
    private_db_name = db.replace('_p', '')
    sql = definer_sql.replace('`', '') \
        .replace('%s.%s.' % (private_db_name, table), '')

    return sql

# We have to parse a specific subset of SQL, that is used to define views
# The Grammar is:
#
# sql = "SELECT" { column-defintions } "FROM" wikiname.tablename [ "WHERE" cond ]
# column-definition = column-name "AS" column-name
#                     | "NULL" "AS" column-name
#                     | "IF(" cond ", NULL, " column-name ")" "AS" column-name
#
# Where cond is a valid SQL relational expression, column-name, wikiname, tablename are strings

identifier = alphanums + "_"
if_definition = "if(" + SkipTo(",")("condition") + "," + Word(identifier) + "," + Word(identifier) + ")"
column_definition = (if_definition ^ Word(identifier)('expression')) + "AS" + Word(identifier)("name") + Optional(",")
sql_definition = "select" + OneOrMore(column_definition)("columns") + \
                 "from" + Word(identifier) + "." + Word(identifier)("tablename") + \
                 Optional("where" + SkipTo(StringEnd())("where")) + StringEnd()


def _table_from_definer(sql, viewname):
    """
    Build a Table object given a cleaned up SQL statement that defines the view
    """
    res = sql_definition.parseString(sql)
    table = Table(viewname, {}, res.where if res.where else None, res.tablename)
    for tokens, start, end in column_definition.scanString(sql):
        table.add_column(Column(tokens.name,
                                whitelisted=tokens.condition == '' and tokens.expression != 'NULL',
                                condition=tokens.condition if tokens.condition else None))

    return table


def views_schema_diff_report(config, model, conn):
    """
    Diff between schema of views in the public db and how they should be
    """
    report = {}
    cur = conn.cursor()
    for db in model.public_dbs:
        report_db = {}
        all_tables = get_tables(conn, db)
        # We want tables that are present in this db and in our model
        # because missing / extra tables are reported from tables.py
        table_names = common_iters(all_tables, model.tables)
        for name in table_names:
            table = model.tables[name]
            cur.execute('SHOW CREATE VIEW %s.%s' % (db, name))
            sql = _cleanup_viewdefiner(cur.fetchone()[1], db, table.table_name)
            t = _table_from_definer(sql, name)
            diff = diff_tables(table, t)
            if diff:
                report_db[name] = diff
        if report_db:
            report[db] = report_db
            logging.info("Differences found in DB %s - %s tables with differences", db, len(report_db))
        else:
            logging.info("No differences found in DB %s", db)
    return report
