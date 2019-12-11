"""
Author:Simon Koch <s9sikoch@stud.uni-saarland.de>
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


class TableUsage():
    def __init__(self, table_name, table_alias):
        self._name = table_name
        self._alias = table_alias


def merge_table_and_columns(tables, columns, logger=None):
    columns = list(set(columns))
    certain = len(tables) == 1
    ret = []
    for table in tables:
        for column in columns:
            ret.append(InteractedSchemaElement(table, column, 'attribute', certain))
    return ret


def parse_function_identifier(function, logger=None):  # COPIED
    tokens = function.tokens
    # fct_name = tokens[0]
    paren = tokens[1]
    ret = []
    for element in paren.get_sublists():
        ret += analyze_select_column_clause_part(element, logger)
    return ret


def parse_select_identifier(identifier, logger=None):   # COPIED
    ret = []
    if type(identifier) == sqlparse.sql.Function:
        ret += parse_function_identifier(identifier)
    if type(identifier) == sqlparse.sql.Identifier:
        if identifier.get_real_name() == 'special':
            # well problem
            pass
        ret += [identifier.get_real_name()]
    return ret


def analyze_select_column_clause_part(stmt, logger=None):  # COPIED
    uses = []
    # print type(stmt)
    if type(stmt) == sqlparse.sql.Identifier:
        uses += parse_select_identifier(stmt)
    elif type(stmt) == sqlparse.sql.IdentifierList:
        for token in stmt.get_identifiers():
            if type(token) == sqlparse.sql.Function:
                uses += parse_function_identifier(token, logger)
            elif type(token) == sqlparse.sql.Identifier:
                uses += parse_select_identifier(token, logger)
            elif type(stmt) == sqlparse.sql.Token and stmt.value == "*":
                uses += ["*"]
            else:
                print "warn: no explicit handling of token {} of type {} in {}".format(token, type(token), stmt)
    elif type(stmt) == sqlparse.sql.Token and stmt.value == "*":
        uses += ["*"]
    else:
        print "warn: no explicit handling of token {} of type {}".format(stmt, type(stmt))
        raise SqlParserDoesNotYetParseThis("boom moddafucker")
    return uses

#    elif token.is_keyword and token.value.upper() in ['DISTINCT', 'DISTINCT']:
#        pass


def position_of_keyword(stmtl, of, pos=0):
    # print "search {} in {} @ {}".format(of, stmtl, pos)
    if len(stmtl) == pos:
        # raise ValueError("list does not contain keyword")
        return None
    else:
        if stmtl[pos].is_keyword and stmtl[pos].value.upper() == of:
            return pos
        elif type(stmtl[pos]) == sqlparse.sql.Where:
            if stmtl[pos].tokens[0].value.upper() == of:
                return pos
        else:
            return position_of_keyword(stmtl, of, pos + 1)


def analyze_parenthesis(stmt, logger=None):  # COPIED
    assert str(stmt.tokens[0].ttype) == 'Token.Punctuation', "first element has to be punctuation"
    assert str(stmt.tokens[-1].ttype) == 'Token.Punctuation', "last element has to be punctuation"
    stmtl = [token for token in stmt.tokens if not token.is_whitespace]
    ret = []
    for token in stmtl[1:-1]:
        if type(token) == sqlparse.sql.Parenthesis:
            ret = ret + analyze_parenthesis(token, logger)
        elif type(token) == sqlparse.sql.Identifier:
            ret.append(token.get_real_name())
        elif token.ttype == sqlparse.tokens.Token.String.Single:
            pass
        elif type(token) == sqlparse.sql.IdentifierList:
            for identifier in token.get_identifiers():
                if identifier.ttype == sqlparse.tokens.Token.String.Single:
                    pass
                else:
                    raise SqlParserDoesNotYetParseThis(
                        "unknwon identifierliste element {} of type {} in {}".format(identifier,
                                                                                     type(identifier),
                                                                                     token.get_identifiers()))
        elif type(token) == sqlparse.sql.Comparison:
            ret.append(token.left.value)
        elif token.is_keyword and token.value.upper() in ['AND', 'OR']:
            pass
        else:
            raise SqlParserDoesNotYetParseThis("unknown paren element {} of type {} in {}".format(token,
                                                                                                  type(token),
                                                                                                  stmt.tokens))
    return ret


def analyze_where_clause_part(stmt, logger=None):  # COPIED
    stmtl = [token for token in stmt.tokens if not token.is_whitespace]
    uses = []
    for token in stmtl:
        if token.is_keyword:
            # might be worth treating LIKE seperately
            if token.value.upper() not in ['WHERE', 'AND', 'OR', 'LIKE', 'IN', 'OR']:
                raise SqlParserDoesNotYetParseThis("got WHERE statement with unknown keyword {} in {}".format(token,
                                                                                                              stmtl))
        elif str(token.ttype) == 'Token.Punctuation':
            pass
        elif type(token) == sqlparse.sql.Comparison:
            uses.append(token.left.value)
        elif type(token) == sqlparse.sql.Identifier:
            uses += [token.get_real_name()]
        elif type(token) == sqlparse.sql.Parenthesis:
            uses += analyze_parenthesis(token, logger)
        elif token.ttype == sqlparse.tokens.Token.String.Single:
            # this means that it is a string and therefore cannot define a column - I hope
            pass
        else:
            raise SqlParserDoesNotYetParseThis("unknown WHERE condition element {} of type {} in {}".format(token,
                                                                                                            type(token),
                                                                                                            stmtl))
    return uses


def analyze_set_clause_part(stmtl, logger=None):  # COPIED
    defines = []
    for token in stmtl[1:]:
        if type(token) == sqlparse.sql.IdentifierList:
            for identifier in token.get_identifiers():
                if identifier.left.is_keyword:
                    defines.append(identifier.left.value)
                else:
                    defines.append(identifier.left.get_real_name())
        elif type(token) == sqlparse.sql.Comparison:
            if type(token.left) == sqlparse.sql.Identifier:
                defines.append(token.left.get_real_name())
            else:
                defines.append(token.right.get_real_name())
        else:
            raise SqlParserDoesNotYetParseThis("unknown {} part in set statement {}".format(token, stmtl))
    return defines


def analyze_from_clause_part(stmtl, logger=None):
    tables = []
    identifiers = []
    if type(stmtl[1]) == sqlparse.sql.IdentifierList:
        identifiers = list(stmtl[1].get_identifiers())
    else:
        identifiers = [stmtl[1]]
    for token in identifiers:
        if type(token) == sqlparse.sql.Identifier:
            tables.append(token.get_real_name())
        else:
            raise SqlParserDoesNotYetParseThis("unknown {} in table definition {}".format(token, stmtl))
    return tables


def analyze_select_statement(select_statement, logger=None):
    stmtl = [token for token in select_statement.tokens if not token.is_whitespace]
    uses = []
    defines = []
    from_pos = position_of_keyword(stmtl, 'FROM')
    where_pos = position_of_keyword(stmtl, 'WHERE')
    if where_pos is None and logger is not None:
        pass
    tables = []
    if where_pos is not None:
        tables = analyze_from_clause_part(stmtl[from_pos:where_pos],
                                          logger)
    elif from_pos is not None and where_pos is None:
        tables = analyze_from_clause_part(stmtl[from_pos:],
                                          logger)
    else:
        pass

    if stmtl[1].is_keyword and (stmtl[1].value.upper() in ['DISTINCT']):
        print "found distinct"
        uses = analyze_select_column_clause_part(stmtl[2], logger)
    else:
        uses = analyze_select_column_clause_part(stmtl[1], logger)
    where_part = [item for item in stmtl if
                  type(item) == sqlparse.sql.Where]
    if len(where_part) == 1:
        uses += analyze_where_clause_part(where_part[0], logger)
    elif logger is not None:
        pass
    uses = merge_table_and_columns(tables, uses, logger)
    return uses, defines


def analyze_into_clause_part(stmtl, logger=None):
    assert len(stmtl) == 2, "into part should not be longer than two %s" % stmtl
    assert stmtl[0].is_keyword, "expected INTO keyword but got %s of type %s" % (stmtl[0],
                                                                                 type(stmtl[0]))
    assert stmtl[0].value == u'INTO', "first part is expected to be INSERT not %s" % stmtl[0]
    return [stmtl[1].get_real_name()], ["*"]


def analyze_insert_statement(insert_statement, logger=None):
    stmtl = [token for token in insert_statement.tokens if not token.is_whitespace]
    uses = []
    defines = []
    pos_into_start = position_of_keyword(stmtl, u'INTO')
    pos_into_end = -1
    if position_of_keyword(stmtl, u'VALUES'):
        pos_into_end = position_of_keyword(stmtl, u'VALUES')
    elif position_of_keyword(stmtl, u'SET'):
        pos_into_end = position_of_keyword(stmtl, u'SET')
    else:
        raise SqlParserDoesNotYetParseThis("How can there no values in insertion? {}".format(stmtl))
    tables, defines = analyze_into_clause_part(stmtl[pos_into_start:pos_into_end],
                                               logger)
    defines = [InteractedSchemaElement(tables[0], "*", 'relation')]
    return uses, defines


def analyze_update_statement(update_statement, logger=None):
    stmtl = [token for token in update_statement.tokens if not token.is_whitespace]
    uses = []
    defines = []
    # print position_of_keyword(stmtl, u'SET')
    tables = analyze_from_clause_part(stmtl[position_of_keyword(stmtl, u'UPDATE'):position_of_keyword(stmtl, u'SET')],
                                      logger)
    uses = analyze_where_clause_part([item for item in stmtl if type(item) == sqlparse.sql.Where][0], logger)
    # this is a bold assumption that the query looks like this
    where_pos = position_of_keyword(stmtl, "WHERE")
    if where_pos is None and logger is not None:
        logger.info("query '{}' has no WHERE part and that is weird".format(stmtl))
    defines = []
    if where_pos is None:
        defines = analyze_set_clause_part(stmtl[position_of_keyword(stmtl, u'SET'):-1])
    else:
        defines = analyze_set_clause_part(stmtl[position_of_keyword(stmtl, u'SET'):where_pos])
    uses = merge_table_and_columns(tables, uses)
    defines = merge_table_and_columns(tables, defines)
    return uses, defines


def analyze_delete_statement(delete_statement, logger=None):
    stmtl = [token for token in delete_statement.tokens if not token.is_whitespace]
    uses = []
    defines = []
    tables = analyze_from_clause_part(stmtl[position_of_keyword(stmtl, u'FROM'):position_of_keyword(stmtl, u'WHERE')])
    assert len(tables) == 1, "there can only be one table being deleted from"
    where_pos = position_of_keyword(stmtl, "WHERE")
    assert where_pos is not None, "query '%s' has no WHERE part and that is unexpected" % stmtl
    uses = analyze_where_clause_part(stmtl[where_pos])
    defines.append(InteractedSchemaElement(tables[0], "*", "attribute"))
    uses = merge_table_and_columns(tables, uses, logger)
    return uses, defines


class SqlQuery():
    _query_string = None
    _defines = None
    _uses = None
    _changing = False

    def __init__(self, query_string, logger=None):
        self._query_string = query_string
        stmt = sqlparse.parse(query_string)[0]
        if stmt.get_type() == 'SELECT':
            self._uses, self._defines = analyze_select_statement(stmt, logger)
        elif stmt.get_type() == 'INSERT':
            self._uses, self._defines = analyze_insert_statement(stmt, logger)
            self._changing = True
        elif stmt.get_type() == 'UPDATE':
            self._uses, self._defines = analyze_update_statement(stmt, logger)
            self._changing = True
        elif stmt.get_type() == 'DELETE':
            self._uses, self._defines = analyze_delete_statement(stmt, logger)
            self._changing = True
        elif stmt.get_type() == 'UNKNOWN':
            raise SqlParserDoesNotParseThis(
                "not yet supported statement type {} in query {}".format(stmt.get_type(), query_string))
        else:
            raise SqlParserDoesNotYetParseThis(
                "not yet supported statement type {} in query {}".format(stmt.get_type(), query_string))

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
