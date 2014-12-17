import argparse
import MySQLdb
import yaml
import re
from datetime import datetime

from dbreflector import DBReflector
from mwconfig import MWConfig
from wikidatabase import WikiDatabase
from table import Table
from column import Column

argparser = argparse.ArgumentParser()

argparser.add_argument('--hosts', help='Hosts to connect to')
argparser.add_argument('--config-file-path', help='Path to config file')
argparser.add_argument('--public', help='Check only public databases, identified by suffix from config',
                       action='store_true')
argparser.add_argument('--output-report-path', help='Path to report.yaml file that should be output')

args = argparser.parse_args()

config = yaml.load(open(args.config_file_path))
mwconfig = MWConfig(config['mediawiki-config-path'])

private_dbs = set(mwconfig.get_dblist('all')) - set(mwconfig.get_dblist('private'))
public_dbs = set([r + config['public-db-suffix'] for r in private_dbs])

if args.public:
    primary_dblist = public_dbs
    secondary_dblist = private_dbs
else:
    primary_dblist = private_dbs
    secondary_dblist = public_dbs

if config['ignore-db-pattern']:
    ignore_db_re = re.compile(config['ignore-db-pattern'])
else:
    ignore_db_re = None
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
        if ignore_db_re and ignore_db_re.match(dbname):
            continue
        all_dbs.add(dbname)
        if dbname not in primary_dblist:
            continue
        db = WikiDatabase(dbname)
        dbs[dbname] = db
        tablenames = reflector.get_tables(dbname)
        for tablename in tablenames:
            if tablename in tables:
                tables[tablename].add_db(db)
            else:
                columnnames = reflector.get_columns(dbname, tablename)
                table = Table(tablename, [Column(cn) for cn in columnnames])
                tables[tablename] = table
                db.add_table(table)

expected_tables = {}
for configfile in config['tableschema-files']:
    configdata = yaml.load(open(configfile))
    for tablename, tabledict in configdata.items():
        expected_tables[tablename] = Table.from_dict(tablename, tabledict)

extra_tables = set(tables.keys()) - set(expected_tables.keys())

extra_columns = {}
for table in tables.values():
    if table.name in expected_tables:
        # Only report if the table is an expected table but has extra columns
        col_diff = set([c.name for c in table.columns]) - set([c.name for c in expected_tables[table.name].columns])
        if col_diff:
            extra_columns[table.name] = list(col_diff)

# Write out report
report = {
    'generated_at': datetime.now().isoformat(),
    'hosts': hostspec,
    'extratables': {tables[table].name: tables[table].dbs.keys() for table in extra_tables},
    'extradbs': list(all_dbs - primary_dblist - secondary_dblist),
    'missingdbs': list(primary_dblist - set(dbs.keys())),
    'extra-columns': extra_columns
}

yaml.dump(report, open(args.output_report_path, 'w'))