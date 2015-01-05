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
import logging
import MySQLdb

from ..utils import get_tables, diff_iters


def _get_extra_tables(model, conn, dbs):
    extra_tables = {}  # K:V :: tablename::list<dbname>
    for db in dbs:
        logging.debug('Finding extra tables on %s', db)
        try:
            extra_tables, _ = diff_iters(get_tables(conn, db), model.tables)
        except MySQLdb.OperationalError as e:
            # Ignore missing database errors (cod 1049).
            # Not using MySQLdb.constants.ER because it is stupid and needs to be explicitly imported to use.
            if e[0] == 1049:
                logging.error('Skipping extra tables check on %s - db not found', db)
                continue  # We have other reports taking care of unknown dbs
            else:
                raise
        if extra_tables:
            for tablename in extra_tables:
                if tablename in extra_tables:
                    extra_tables[tablename].append(db)
                else:
                    extra_tables[tablename] = [db]
    return extra_tables


def extra_tables_report(config, model, conn):
    return {
        'extra_tables_public_dbs': _get_extra_tables(model, conn, model.public_dbs),
        'extra_tables_private_dbs': _get_extra_tables(model, conn, model.private_dbs)
    }
