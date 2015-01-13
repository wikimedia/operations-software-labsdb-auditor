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
import time

import MySQLdb
from labsdb.auditor.models import Model


class ReportRunner(object):
    """
    Runs a set of reports!
    """
    def __init__(self, config):
        self.model = Model.from_config(config['tableschema-files'], config['mediawiki-config-path'])
        self.config = config
        self._reporters = {}

    def register_report(self, func):
        """
        Decorator to register a function as a report builder
        """
        self._reporters[func.__name__] = {
            'name': func.__name__,
            'description': func.__doc__,
            'func': func
        }
        return func

    def run(self):
        all_reports = []
        for host in self.config['hosts']:
            logging.info('Generating reports for host %s', host)
            conn = MySQLdb.connect(host=host, read_default_file='~/.my.cnf')

            host_report = {
                'host': host,
                'reports': []
            }
            for name, reporter in self._reporters.items():
                start_time = time.time()
                report = reporter['func'](self.config, self.model, conn)
                host_report['reports'].append({
                    'name': name,
                    'report': report
                })
                elapsed_time = time.time() - start_time
                logging.info('Generated %s for %s in %s', name, host, elapsed_time)

            conn.close()

            all_reports.append(host_report)
        return all_reports
