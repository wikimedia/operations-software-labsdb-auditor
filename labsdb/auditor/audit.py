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
Script to verify that LabsDB is as clean as it should be.

It takes as input a 'model' of how LabsDB should be, including:

    - Databases which should exist
    - Tables that should exist
    - Columns that must be conditionally nulled in tables
    - Columns that must be unconditionally nulled in tables

It outputs a series of reports, run for each labsdb host. Each
report gets a mysql connection, and the model of how things should
be, and simply outputs a dict with its report.
"""
import argparse
import logging
import os

import yaml
from runner import ReportRunner
from reports.databases import databases_report
from labsdb.auditor.reports.tables import extra_tables_report
from labsdb.auditor.utils import diff_iters
from labsdb.auditor.models import Model, Table
from reports.viewdiffs import views_schema_diff_report


argparser = argparse.ArgumentParser()

argparser.add_argument('--config-file-path', help='Path to config file', default='config.yaml')
argparser.add_argument('--output-file-path', help='Path to report output file', default='report.yaml')
argparser.add_argument('--log-file-path', help='Path to log file', default='audit.log')
argparser.add_argument('--debug', action='store_true', help='Turn on debug logging')
argparser.add_argument('--ignore-public-dbs', action='store_true',
                       help='Ignore public dbs (useful for running against sanitarium)')

args = argparser.parse_args()

with open(args.config_file_path) as cf:
    config = yaml.load(cf)


logging.basicConfig(filename=args.log_file_path,
                    level=logging.DEBUG if args.debug else logging.INFO,
                    format='%(asctime)s: %(message)s'
                    )

# Load up the model
tables = {}
for ts_path in config['tableschema-files']:
    with open(ts_path) as ts:
        tableschema = yaml.load(ts)
    for tablename, tabledict in tableschema.items():
        tables[tablename] = Table.from_dict(tablename, tabledict)

mwconf_path = config['mediawiki-config-path']
all_dblist_path = os.path.join(mwconf_path, 'all.dblist')
private_dblist_path = os.path.join(mwconf_path, 'private.dblist')

with open(all_dblist_path) as all_file, open(private_dblist_path) as priv_file:
    all_wiki_dbs = [l.strip() for l in all_file.readlines()]
    priv_wiki_dbs = [l.strip() for l in priv_file.readlines()]
    dbs, _ = diff_iters(all_wiki_dbs, priv_wiki_dbs)

private_dbs = dbs
public_dbs = [db + '_p' for db in private_dbs] if not args.ignore_public_dbs else []

model = Model(private_dbs, public_dbs, tables)

rr = ReportRunner(config, model)

rr.register_report(databases_report)
rr.register_report(extra_tables_report)
rr.register_report(views_schema_diff_report)

logging.info('Starting report generation')
reports = rr.run()

with open(args.output_file_path, 'w') as f:
    yaml.dump(reports, f)

logging.info('Finished report generation, output written to %s', args.output_file_path)
