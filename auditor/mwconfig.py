import os

class MWConfig(object):
    """
    Represents settings that can be read from mediawiki-config git repository
    """

    def __init__(self, path):
        self.path = path

    def get_dblist(self, listname):
        """
        Get list of databases specified in a particular dblist

        :param listname: Name of dblist (eg. wikipedia, special)
        :return: List of databases in that dblist
        """
        path = os.path.join(self.path, listname + '.dblist')
        with open(path) as f:
            return [l.strip() for l in f.readlines()]
