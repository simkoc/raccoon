"""
Author:Simon Koch <s9sikoch@stud.uni-saarland.de>
This file contains the code to extract relevant needed
information out of the pseudo-parsetree returned
by sqlparse. However, it relies on a modified fork
of the official repository:
https://github.com/simkoc/sqlparse
"""

import sqlparse
import hashlib
from exceptions import SqlParserDoesNotParseThis, SqlParserDoesNotYetParseThis


class InteractedSchemaElement():
    def __init__(self, table, value, t, certain=True):
        self._table = table
        self._value = value
        self._certain = certain
        self._type = t  # may be of attribute or relation

    def intersects(self, other):
        table_p = self._table == other._table
        column_p = False
        if self._value == "*" or other._value == "*":
            column_p = True
        elif self._value == other._value:
            column_p = True
        return table_p and column_p

    def __eq__(self, other):
        return self._table == other._table and self._value == other._value and self._type == other._type

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return "{}.{}({})".format(self._table, self._value, "C" if self._certain else "U")

    def __repr__(self):
        return self.__str__()


def merge_table_and_columns(tables, columns, logger=None):
    columns = list(set(columns))
    certain = len(tables) == 1
    ret = []
    for table in tables:
        # print table
        if table[0] == '`':
            table = table[1:]
        if table[-1] == '`':
            table = table[0:-1]
        for column in columns:
            ret.append(InteractedSchemaElement(table, column, 'attribute', certain))
    return ret


def position_of_keyword(stmtl, of, pos=0):
    if len(stmtl) == pos:
        return None
    else:
        if stmtl[pos].is_keyword and stmtl[pos].value.upper() == of:
            return pos
        elif type(stmtl[pos]) == sqlparse.sql.Where:
            if stmtl[pos].tokens[0].value.upper() == of:
                return pos
        else:
            return position_of_keyword(stmtl, of, pos + 1)


def analyze_identifier_list(identlist, keywords_are_identifiers=False, logger=None):
    """
    This function is the bread and butter of the analyzer as
    this function does the actual analysis and is called (recursively)
    by all other functions that deal with (sub)parts of a given
    pseudo-parsetree. If anything breaks - it does so here
    """
    if identlist is None:
        identlist = []
    ret = []
    for token in identlist:
        if type(token) == sqlparse.sql.Function:
            ret += analyze_function(token, logger)
        elif type(token) == sqlparse.sql.Identifier:
            if token.get_real_name() == 'special':
                pass
            else:
                ret.append(token.get_real_name())
        elif type(token) == sqlparse.sql.Token and token.value == "*":
            ret += ["*"]
        elif type(token) == sqlparse.sql.Parenthesis:
            ret += analyze_parenthesis(token, logger)
        elif type(token) == sqlparse.sql.Operation:
            ret += analyze_identifier_list(token.tokens,
                                           keywords_are_identifiers=True)
        elif type(token) == sqlparse.sql.IdentifierList:
            ret += analyze_identifier_list(token.get_identifiers())
        elif token.ttype == sqlparse.tokens.Token.String.Single:
            pass
        elif token.ttype == sqlparse.tokens.Token.Operator:
            pass
        elif type(token) == sqlparse.sql.Comparison:
            ret += analyze_identifier_list([token.left], keywords_are_identifiers=True, logger=logger)
            ret += analyze_identifier_list([token.right], keywords_are_identifiers=True, logger=logger)
        elif token.is_keyword:
            if keywords_are_identifiers:
                ret += token.value
            else:
                pass
        elif token.is_whitespace:
            pass   # whitespaces are of no interest for our purposes
        elif str(token.ttype) == "Token.Literal.Number.Integer":
            pass   # fixed values are of no interest for our purposes
        else:
            raise SqlParserDoesNotYetParseThis("token {} in list {} unknown".format(token, identlist))
    return ret


def analyze_function(function, logger=None):
    assert type(function) == sqlparse.sql.Function, "this function expects a function"
    return analyze_identifier_list(function.get_parameters(),
                                   keywords_are_identifiers=True,
                                   logger=logger)


def analyze_parenthesis(token, logger=None):
    assert str(token.tokens[0].ttype) == 'Token.Punctuation', "first element has to be punctuation"
    assert str(token.tokens[-1].ttype) == 'Token.Punctuation', "last element has to be punctuation"
    return analyze_identifier_list(token.tokens[1:-1], logger=logger)


def get_from_sublist(token_list, logger=None):
    pos_from = position_of_keyword(token_list, 'FROM')
    pos_where = position_of_keyword(token_list, 'WHERE')
    pos_group = position_of_keyword(token_list, 'GROUP')
    pos_having = position_of_keyword(token_list, 'HAVING')
    pos_order = position_of_keyword(token_list, 'ORDER')
    pos_limit = position_of_keyword(token_list, 'LIMIT')
    ll = [pos_where, pos_group, pos_having, pos_order, pos_limit]
    ll = [elem for elem in ll if elem is not None]
    if len(ll) != 0:
        return token_list[pos_from+1:ll[0]], True if pos_group is not None else False
    else:
        return token_list[pos_from+1:], True if pos_group is not None else False


def analyze_select_statement(token_list, logger=None):
    token_list = [token for token in token_list if not token.is_whitespace]
    uses = []
    defines = []
    from_sublist, aggregate_p = get_from_sublist(token_list, logger)
    tables = analyze_identifier_list(from_sublist,
                                     keywords_are_identifiers=True,
                                     logger=logger)
    if token_list[1].is_keyword and token_list[1].value.upper() in ['DISTINCT']:
        uses = analyze_identifier_list(token_list[2:3],
                                       keywords_are_identifiers=True,
                                       logger=logger)
    else:
        uses = analyze_identifier_list(token_list[1:2],
                                       keywords_are_identifiers=True,
                                       logger=logger)
    where = [item for item in token_list if type(item) == sqlparse.sql.Where]
    if len(where) == 1:
        uses += analyze_identifier_list(where[0].tokens)
    uses = merge_table_and_columns(tables, uses, logger)
    return uses, defines, aggregate_p


def extract_insert_table_identifier(token_list, logger=None):
    assert len(token_list) == 1, "the list must not be longer or shorter than 1"
    if type(token_list[0]) == sqlparse.sql.Function:
        return [token_list[0].get_name()]
    elif type(token_list[0]) == sqlparse.sql.Identifier:
        return [token_list[0].get_real_name()]
    else:
        raise SqlParserDoesNotYetParseThis(
            "got {} but expected function or identifier as into value".format(token_list[0]))


def analyze_insert_statement(token_list, logger=None):
    token_list = [token for token in token_list if not token.is_whitespace]
    tables = []

    if token_list[1].is_keyword:  # this is needed to remove that pesky ignore
        if token_list[1].value.upper() == 'IGNORE':
            token_list = token_list[0:1] + token_list[2:]

    if token_list[1].is_keyword:
        if token_list[1].value.upper() == 'INTO':
            tables = extract_insert_table_identifier(token_list[2:3], logger=logger)
        else:
            raise SqlParserDoesNotYetParseThis("there should only be INTO and not '{}' in {}".format(token_list[1],
                                                                                                     token_list))
    else:
        tables = extract_insert_table_identifier(token_list[1:2], logger=logger)
    return [], merge_table_and_columns(tables, "*", logger)


def analyze_update_statement(token_list, logger=None):
    token_list = [token for token in token_list if not token.is_whitespace]
    uses = []
    defines = []
    pos_update = position_of_keyword(token_list, 'UPDATE')
    pos_set = position_of_keyword(token_list, 'SET')
    tables = analyze_identifier_list(token_list[pos_update+1:pos_set],
                                     keywords_are_identifiers=True,
                                     logger=logger)
    pos_where = position_of_keyword(token_list, 'WHERE')
    if pos_where is not None:
        uses = analyze_identifier_list(token_list[pos_where].tokens)
        defines = analyze_identifier_list(token_list[pos_set:pos_where])
    else:
        defines = analyze_identifier_list(token_list[pos_set:-1])
    uses = merge_table_and_columns(tables, uses, logger)
    defines = merge_table_and_columns(tables, defines, logger)
    return uses, defines


def analyze_delete_statement(token_list, logger=None):
    token_list = [token for token in token_list if not token.is_whitespace]
    uses = []
    defines = []
    pos_from = position_of_keyword(token_list, 'FROM')
    pos_where = position_of_keyword(token_list, 'WHERE')
    # assert pos_where is not None, "it does not make sense to have DELETE clause without where - does it?"
    if pos_where is not None:
        tables = analyze_identifier_list(token_list[pos_from+1:pos_where],
                                         keywords_are_identifiers=True,
                                         logger=logger)
        uses = analyze_identifier_list(token_list[pos_where].tokens)
    else:
        tables = analyze_identifier_list(token_list[pos_from+1:],
                                         keywords_are_identifiers=True,
                                         logger=logger)
        uses = ["*"]
    defines.append(InteractedSchemaElement(tables[0], "*", "relation"))
    uses = merge_table_and_columns(tables, uses, logger)
    return uses, defines


class SqlQuery():
    _query_string = None
    _defines = None
    _uses = None
    _changing = False
    _aggregate_p = False
    _dml_type = None

    def __init__(self, query_string, logger=None):
        self._query_string = query_string
        stmt = sqlparse.parse(query_string)[0]
        if stmt.get_type() == 'SELECT':
            # print "parsing SELECT"
            self._uses, self._defines, self._aggregate_p = analyze_select_statement(stmt.tokens, logger)
            # print self
        elif stmt.get_type() == 'INSERT':
            self._uses, self._defines = analyze_insert_statement(stmt.tokens, logger)
            self._changing = True

        elif stmt.get_type() == 'REPLACE':
            self._uses, self._defines = analyze_insert_statement(stmt.tokens, logger)
            self._changing = True

        elif stmt.get_type() == 'UPDATE':
            self._uses, self._defines = analyze_update_statement(stmt.tokens, logger)
            self._changing = True

        elif stmt.get_type() == 'DELETE':
            self._uses, self._defines = analyze_delete_statement(stmt.tokens, logger)
            self._changing = True

        elif stmt.get_type() == 'UNKNOWN':
            raise SqlParserDoesNotParseThis(
                "not yet supported statement type {} in query {}".format(stmt.get_type(), query_string))
        else:
            raise SqlParserDoesNotYetParseThis(
                "not yet supported statement type {} in query {}".format(stmt.get_type(), query_string))

        self._defines = sorted(self._defines, key=lambda x: x.__str__)
        self._uses = sorted(self._uses, key=lambda x: x.__str__)

    def __str__(self):
        return "<{} D:{} U:{}>".format(self._query_string, self._defines, self._uses)

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return int(hashlib.sha224(self._query_string).hexdigest(), 16)

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def interdependent(self, other):
        return True if len(self.get_intersection(other)) > 0 else False

    def get_intersection(self, other):
        try:
            intersection = []
            for inter in self._uses:
                matches = [m for m in other._defines if inter.intersects(m)]
                intersection += matches
        except Exception:
            print other
            print self
            raise
        return intersection

    def get_intersection_inv(self, other):
        try:
            intersection = []
            for inter in other._defines:
                matches = [m for m in self._uses if inter.intersects(m)]
                intersection += matches
        except Exception:
            print other
            print self
            raise
        return intersection

    # def abstract(self):
        # drop anything on thre right side of comparison/leq/geq
