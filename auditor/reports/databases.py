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

from auditor.utils import get_databases


def databases_report(config, model, conn):
    """
    Diff of what databases exist on labsdb and what should

    Inlcudes:

        - extra_dbs -> DBs that are in labsdb but shouldn't be
        - missing_private_dbs -> Fully Replicated DBs that should be in labsdb but aren't
        - missing_public_dbs -> Publicly Viewable DBs that should be in labsdb but aren't
    """
    server_dbs = get_databases(conn)
    # Both the private databases and the _p variants that are accessible to public
    whitelisted_dbs = model.public_dbs + model.private_dbs
    ignore_re = re.compile(config['user-dbname-regex'])
    extra_dbs = [db for db in server_dbs if db not in whitelisted_dbs and not ignore_re.match(db)]
    missing_public_dbs = [db for db in model.public_dbs if db not in server_dbs]
    missing_private_dbs = [db for db in model.private_dbs if db not in server_dbs]
    return {
        'extra_dbs': extra_dbs,
        'missing_private_dbs': missing_private_dbs,
        'missing_public_dbs': missing_public_dbs,
    }
