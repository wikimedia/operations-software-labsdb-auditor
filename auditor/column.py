class Column(object):
    """
    Represents a particular column in a particular table.
    """
    def __init__(self, name, whitelisted=True, condition=None, replacewith=None):
        """
        Create a new column

        :param name: Name of this column
        :param whitelisted: True if the column is whitelisted
        :param condition: Conditions under which this column is replaced
        :param replacewith: What to replace the column's value with if condition is matched
        :return:
        """
        self.name = name
        self.whitelisted = whitelisted
        self.condition = condition
        self.replacewith = replacewith

