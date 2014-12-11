class Table(object):
    def __init__(self, name, columns):
        self.name = name
        self.columns = columns
        self.dbs = {}

    def add_db(self, db):
        if db.name in self.dbs:
            return
        self.dbs[db.name] = db
        db.add_table(self)
