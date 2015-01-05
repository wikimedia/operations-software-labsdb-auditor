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
import yaml
import os


class Column(object):
    """
    A column that is potentially conditionally or unconditionally nulled
    """
    def __init__(self, name, whitelisted=True, condition=None, replacewith=None):
        """
        A column in a table that can be whitelisted or conditionally nulled

        if whitelisted is True, the other parameters will have no effect.

        :param name: Name of this column
        :param whitelisted: True if the column is whitelisted
        :param condition: Conditions under which this column is replaced.
                          Specified as a string that is valid SQL expression
        :param replacewith: What to replace the column's value with if condition is matched
                            If set to None with whitelisted = False, implies SQL None
        :return:
        """
        self.name = name
        self.whitelisted = whitelisted
        self.condition = condition
        self.replacewith = replacewith


class Table(object):
    def __init__(self, name, columns=[], where=None, table_name=None):
        self.name = name
        self.columns = columns
        self.where = where
        self.table_name = table_name if table_name else name

    def add_column(self, column):
        self.columns.append(column)
        column.table = self

    def to_dict(self):
        """
        Convert Table to a minimal dict from which it can be reconstituted
        """
        tabledict = {}
        if self.where:
            tabledict['where'] = self.where
        if all([c.whitelisted for c in self.columns]):
            # Everything is whitelisted!
            tabledict['columns'] = [c.name for c in self.columns]
        else:
            tabledict['columns'] = {}
            for c in self.columns:
                columndict = {}
                columndict['whitelisted'] = c.whitelisted
                if c.condition:
                    columndict['condition'] = c.condition
                if c.replacewith:
                    columndict['replacewith'] = c.replacewith
                tabledict['columns'][c.name] = columndict
        if self.table_name != self.name:
            tabledict['table_name'] = self.table_name
        return tabledict

    @classmethod
    def from_dict(cls, tablename, tabledata):
        table = cls(tablename, [], tabledata.get('where', None), tabledata.get('table_name', None))
        if isinstance(tabledata['columns'], list):
            # Whitelisted table
            for colname in tabledata['columns']:
                table.add_column(Column(colname))
        else:
            # Greylisted table!
            for colname, coldata in tabledata['columns'].items():
                table.add_column(Column(colname, False, coldata.get('condition'), coldata.get('replacewith')))
        return table


class Model(object):
    """
    A complete model of how a labsdb should be.

    Contains:
        - List of dbs that should exist (list)
        - List of tables that can exist in any db (dict with tablename as key)
    """
    def __init__(self, dblist, tables):
        self.private_dbs = dblist
        self.public_dbs = [db + '_p' for db in dblist]
        self.tables = tables

    @classmethod
    def from_config(cls, tableschema_files, mwconf_path):
        """
        Creates a Model from a given config

        Reads table schema from schema files and sets up appropriate tables.
        Reads dblists from mediawiki-config repo
        :param tableschema_files: List of files to read table schema from
        :param mwconf_path: Path to check out of mediawiki-config repository
        """
        tables = {}
        for ts_path in tableschema_files:
            with open(ts_path) as ts:
                tableschema = yaml.load(ts)
            for tablename, tabledict in tableschema.items():
                tables[tablename] = Table.from_dict(tablename, tabledict)

        all_dblist_path = os.path.join(mwconf_path, 'all.dblist')
        private_dblist_path = os.path.join(mwconf_path, 'private.dblist')

        with open(all_dblist_path) as all_file, open(private_dblist_path) as priv_file:
            all_dbs = [l.strip() for l in all_file.readlines()]
            priv_dbs = [l.strip() for l in priv_file.readlines()]
            dbs = list(set(all_dbs) - (set(priv_dbs)))

        return cls(dbs, tables)
