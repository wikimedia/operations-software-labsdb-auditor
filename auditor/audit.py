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
import yaml

from runner import ReportRunner

from reports.databases import databases_report
from reports.tables import extra_tables_report


argparser = argparse.ArgumentParser()

argparser.add_argument('--config-file-path', help='Path to config file', default='config.yaml')
argparser.add_argument('--output-file-path', help='Path to report output file', default='report.yaml')
argparser.add_argument('--log-file-path', help='Path to log file', default='audit.log')
argparser.add_argument('--debug', action='store_true', help='Turn on debug logging')

args = argparser.parse_args()

with open(args.config_file_path) as cf:
    config = yaml.load(cf)


logging.basicConfig(filename=args.log_file_path,
                    level=logging.DEBUG if args.debug else logging.INFO,
                    format='%(asctime)s: %(message)s'
                    )

rr = ReportRunner(config)

rr.register_report(databases_report)
rr.register_report(extra_tables_report)

logging.info('Starting report generation')
reports = rr.run()

with open(args.output_file_path, 'w') as f:
    yaml.dump(reports, f)

logging.info('Finished report generation, output written to %s', args.output_file_path)
