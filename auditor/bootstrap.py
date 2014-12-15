import sys
import argparse
import MySQLdb
import yaml

from dbreflector import DBReflector
from mwconfig import MWConfig
from wikidatabase import WikiDatabase
from table import Table

argparser = argparse.ArgumentParser()

argparser.add_argument('--hosts', help='Hosts to connect to')
argparser.add_argument('--mwconfig', help='Path to mediawiki-config repository')
argparser.add_argument('--db_suffix', help='Suffix to use for each database name',
                       default='')

args = argparser.parse_args()

mwconfig = MWConfig(args.mwconfig)

raw_whitelist_dbs = set(mwconfig.get_dblist('all')) - set(mwconfig.get_dblist('private'))
whitelist_dbs = set([r + args.db_suffix for r in raw_whitelist_dbs])

all_dbs = set()

dbs = {}
tables = {}

hostspec = args.hosts.split(',')
for host in hostspec:
    if ':' in host:
        hostname, port = host.split(':')
        port = int(port)
    else:
        hostname, port = host, 3306
    conn = MySQLdb.connect(host=hostname, port=port, read_default_file='~/.my.cnf')
    reflector = DBReflector(conn)
    dbnames = reflector.get_databases()
    for dbname in dbnames:
        all_dbs.add(dbname)
        if dbname not in whitelist_dbs:
            continue
        db = WikiDatabase(dbname)
        dbs[dbname] = db
        tablenames = reflector.get_tables(dbname)
        for tablename in tablenames:
            if tablename in tables:
                tables[tablename].add_db(db)
            else:
                table = Table(tablename, reflector.get_columns(dbname, tablename))
                tables[tablename] = table
                db.add_table(table)

# Write out db lists
yaml.dump({
    'not-in-db': list(whitelist_dbs - set(dbs.keys())),
    'not-in-dblist': list(all_dbs - whitelist_dbs - raw_whitelist_dbs)
}, open('dblists.yaml', 'w'))

# Write out table schemas
schemadata = {}
for name, table in tables.items():
    tabledata = {}
    for columnname in table.columns:
        tabledata[columnname] = {'whitelisted': True}
    schemadata[name] = tabledata

yaml.dump(schemadata, open('tableschema.yaml', 'w'))