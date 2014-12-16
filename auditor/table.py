from column import Column

class Table(object):
    def __init__(self, name, columns=[], where=None):
        self.name = name
        self.dbs = {}
        self.columns = columns
        self.where = where

    def add_db(self, db):
        if db.name in self.dbs:
            return
        self.dbs[db.name] = db
        db.add_table(self)

    def add_column(self, column):
        self.columns.append(column)
        column.table = self

    def to_dict(self):
        tabledict = {}
        if self.where:
            tabledict['where'] = self.where
        if all([c.whitelisted for c in self.columns]):
            # Everything is whitelisted!
            tabledict['columns'] = [c.name for c in self.columns]
        else:
            tabledict['columns'] = {}
            for c in self.columns:
                columndict = {}
                columndict['whitelisted'] = c.whitelisted
                if c.condition:
                    columndict['condition'] = c.condition
                if c.replacewith:
                    columndict['replacewith'] = c.replacewith
                tabledict['columns'][c.name] = columndict
        return tabledict

    @classmethod
    def from_dict(cls, tablename, tabledata):
        table = cls(tablename, tabledata.get('where', None))
        if isinstance(tabledata['columns'], list):
            # Whitelisted table
            for colname in tabledata['columns']:
                table.add_column(Column(colname))
        else:
            # Greylisted table!
            for colname, coldata in tabledata['columns'].items():
                table.add_column(Column(colname, False, coldata.get('condition'), coldata.get('replacewith')))
