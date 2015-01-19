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
"""
Contains classes that Model how LabsDB should be
"""


class Column(object):
    """
    A column that is potentially conditionally or unconditionally nulled
    """
    def __init__(self, name, whitelisted=True, null_if=None):
        """
        A column in a table that can be whitelisted or conditionally nulled

        if whitelisted is True, the other parameters will have no effect.

        :param name: Name of this column
        :param whitelisted: True if the column is whitelisted
        :param null_if: Conditions under which this column is nulled.
                        Specified as a string that is valid SQL expression.
                        If set to None & whitelisted=False, then nulled all the time

        :return:
        """
        self.name = name
        self.whitelisted = whitelisted
        self.null_if = null_if


class Table(object):
    def __init__(self, name, columns={}, include_row_if=None, table_name=None):
        self.name = name
        self.columns = columns
        self.include_row_if = include_row_if
        self.table_name = table_name if table_name else name

    def add_column(self, column):
        self.columns[column.name] = column

    def to_dict(self):
        """
        Convert Table to a minimal dict from which it can be reconstituted
        """
        tabledict = {}
        if self.include_row_if:
            tabledict['include_row_if'] = self.include_row_if
        if all([c.whitelisted for c in self.columns.values()]):
            # Everything is whitelisted!
            tabledict['columns'] = [c.name for c in self.columns]
        else:
            tabledict['columns'] = {}
            for c in self.columns.values():
                columndict = {}
                columndict['whitelisted'] = c.whitelisted
                if c.null_if:
                    columndict['null_if'] = c.null_if
                tabledict['columns'][c.name] = columndict
        if self.table_name != self.name:
            tabledict['table_name'] = self.table_name
        return tabledict

    @classmethod
    def from_dict(cls, tablename, tabledata):
        table = cls(tablename, {}, tabledata.get('include_row_if', None), tabledata.get('table_name', None))
        if isinstance(tabledata['columns'], list):
            # Whitelisted table
            for colname in tabledata['columns']:
                table.add_column(Column(colname))
        else:
            # Greylisted table!
            for colname, coldata in tabledata['columns'].items():
                col = Column(colname, coldata.get('whitelisted'), coldata.get('null_if'))
                table.add_column(col)
        return table


class Model(object):
    """
    A complete model of how a labsdb should be.

    Contains:
        - List of dbs that should exist (list)
        - List of tables that can exist in any db (dict with tablename as key)
    """
    def __init__(self, private_dbs, public_dbs, tables):
        self.private_dbs = private_dbs
        self.public_dbs = public_dbs
        self.tables = tables
