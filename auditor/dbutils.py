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
Collection of utilities for dealing with databases
"""


def get_databases(conn):
    """
    Get list of databases in given connection
    """
    cur = conn.cursor()
    cur.execute('SHOW DATABASES')
    dbs = [r[0] for r in cur.fetchall()]
    cur.close()
    return dbs


def get_tables(conn, dbname):
    """
    Get list of tables in given database
    """
    cur = conn.cursor()
    # Uh oh, this triggers my OMG SQLATTACK sensitibilities,
    # but you can not use parameterized queries for USE
    # FIXME: Find out how to quote this manually, and quote it
    cur.execute('USE %s' % (dbname, ))
    cur.execute('SHOW TABLES')
    tables = [r[0] for r in cur.fetchall()]
    cur.close()
    return tables
