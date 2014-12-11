class DBReflector(object):
    """
    Provides methods to gather metadata about objects in a database server
    """
    def __init__(self, conn):
        self.conn = conn

    def get_databases(self):
        """
        Get list of databases in given server

        :return: List of databases from current server
        """
        cur = self.conn.cursor()
        cur.execute("SHOW DATABASES")
        results = [r[0] for r in cur.fetchall()]
        cur.close()
        return results

    def get_tables(self, dbname):
        """
        Get list of tables in given database

        :arg dbname: Name of database to get tables list for
        :return: List of tables in given database
        """
        cur = self.conn.cursor()
        cur.execute('USE ' + dbname)  # Can't do %s for USE, sigh
        cur.execute("SHOW TABLES")
        results = [r[0] for r in cur.fetchall()]
        cur.close()
        return results

    def get_columns(self, dbname, tablename):
        """
        Get list of columns in given table in given database

        :param dbname: Name of database to find table name
        :param tablename: Table to get columns list for
        :return: List of columns for the given table
        """
        cur = self.conn.cursor()
        cur.execute('USE ' + dbname)  # Can't do %s for USE, sigh
        cur.execute('DESCRIBE ' + tablename)
        results = [r[0] for r in cur.fetchall()]
        cur.close()
        return results
