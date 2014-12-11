class WikiDatabase(object):
    """
    Represents a particular wiki's database
    """
    def __init__(self, name):
        self.name = name
        self.tables = {}

    @property
    def publicdbname(self):
        return self.dbname + '_p'

    def add_table(self, table):
        """
        Add a table to the current database
        :param table: Table object to add
        """
        if table.name in self.tables:
            return
        self.tables[table.name] = table
        table.add_db(self)

