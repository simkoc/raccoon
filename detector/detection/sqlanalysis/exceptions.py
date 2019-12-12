""""
This file contains all the exceptions that should be expected to be
thrown by the sql parsing module
"""


class SqlParserDoesNotYetParseThis(ValueError):
    """This exception is raised if the sqlparser returns NONE as a statement after check syntax"""

    def __init__(self, message):
        self.message = message
        super(SqlParserDoesNotYetParseThis, self).__init__(message)


class SqlParserDoesNotParseThis(ValueError):
    """This exception is raised if the sqlparser returns NONE as a statement after check syntax"""

    def __init__(self, message):
        self.message = message
        super(SqlParserDoesNotParseThis, self).__init__(message)


class ViolatedSqlSyntaxException(ValueError):
    """This exception is raised if the sqlparser does not like the synatax of a given SQL query"""

    def __init__(self, message):
        self.message = message
        super(ViolatedSqlSyntaxException, self).__init__(message)


class ParserDebugException(ValueError):
    """This exception can be raised to stop at certain debug points"""

    def __init__(self, message):
        self.message = message
        super(ParserDebugException, self).__init__(message)
