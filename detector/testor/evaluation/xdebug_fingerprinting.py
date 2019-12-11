import sqlnorm


class QueryParameter():

    def __init__(self, name, value):
        self._name = name
        self._value = value


def query_parameter_surjective_equal(lhs, rhs, constantp):
    if not constantp:
        return lhs._name == rhs._name
    else:
        return (lhs._name == rhs._name and
                lhs._value == rhs._value)


class PaQu():

    def __init__(self, paqu, logger=None):
        self._path = paqu.split("?")[0]
        parameters = paqu.split("?")[1] if len(paqu.split("?")) == 2 else ""
        buff = []
        if parameters != "":
            for parameter in parameters.split("&"):
                if len(parameter.split("=")) == 2:
                    buff.append(QueryParameter(parameter.split("=")[0],
                                               parameter.split("=")[1]))
                else:
                    if logger is not None:
                        logger.info("parameter in url does not have rhs: {}".format(parameter))
                    buff.append(QueryParameter(parameter.split("=")[0],
                                               ""))

        self._parameters = {}
        for elem in buff:
            self._parameters[elem._name] = elem

    def __str__(self):
        ret = self._path
        if len(self._parameters) != 0:
            ret = "{}?".format(ret)
        for key, value in self._parameters.iteritems():
            ret = "{}{}={}&".format(ret, key, value._value)
        return ret[:-1]

    def __repr__(self):
        return self.__str__()


def paqu_surjective_equal_p(lhs, rhs, constant_oracle=lambda x: False, logger=None):
    # check if the paths match
    if lhs._path != rhs._path:
        return False, "request {} Region 2 uses a different path than {}".format(rhs, lhs)
    # check if the sets of query parameter names are equal
    if set(rhs._parameters.keys()) != set(lhs._parameters.keys()):
        return False, "request {} contains different query parameters than {}".format(rhs, lhs)
    # iterate over all paramters contained by rhs
    for key, value in rhs._parameters.iteritems():
        # check if parameter name exists in lhs query
        if key in lhs._parameters:
            # if exists check if parameter is surjective equal
            if query_parameter_surjective_equal(lhs._parameters[key],
                                                value,
                                                constant_oracle(key)):
                # well parameter is equal consequently continue
                pass
            else:
                # parameter is not surjective equal, abort with
                # false for equality and true for true mismatch
                return False, "constant parameter '{}' mismatch for requests {} and {}".format(key, lhs, rhs)
        # if does not exist queries cannot be equal
        else:
            # parameter was unknown
            False, "parameter '{}' of {} was not found in {}".format(key, rhs, lhs)
    return True, "request uri {} is similiar to {}".format(rhs, lhs)


class XdebugFingerprint:

    def __init__(self, xdebug, paQu):
        if type(xdebug) is tuple:
            raise Exception("this is a problem - xdebug should not be a tuple")
        self._queries = xdebug.get_sql_queries()
        self._url = paQu

    def check_fingerprint(self):
        if len(self._queries) == 0:
            return False
        else:
            return True

    def __str__(self):
        str = "Query count: {}\n".format(len(self._queries))
        str += "Path: {}".format(self._url)
        return str


def queries_surjective_equal_p(fprintlhs, fprintrhs, logger=None):
    cqueries, waste = fprintlhs._queries
    no_mismatch_reason = "no reason"

    if len(cqueries) == 0:
        if logger is not None:
            logger.debug("there are 0 queries contained in the comp xdebug")
        if len(fprintrhs._queries) == 0:
            if logger is not None:
                logger.debug("self xdebug contains 0 queries as well")
            return True, no_mismatch_reason
        else:
            return False, "not equal query amount"
    cqueriesh = [sqlnorm.generate_normalized_query_hash(query)
                 for query in cqueries]
    comp_queriesh, comp_queries = [list(x) for x in
                                   zip(*sorted(zip(cqueriesh, cqueries),
                                               key=lambda pair: pair[0]))]
    oqueries, garbage = fprintrhs._queries
    oqueriesh = [sqlnorm.generate_normalized_query_hash(query)
                 for query in oqueries]
    own_queriesh, own_queries = [list(x) for x in
                                 zip(*sorted(zip(oqueriesh, oqueries),
                                             key=lambda pair: pair[0]))]
    if len(comp_queries) != len(own_queries):
        if logger is not None:
            return False, "different query amount"
    for cqh, cq, oqh, oq in zip(comp_queriesh, comp_queries,
                                own_queriesh, own_queries):
        if cqh != oqh:
            if logger is not None:
                logger.debug("query {}({}) mismatches {}({})".format(cq,
                                                                     cqh,
                                                                     oq,
                                                                     oqh))
            return False, "query {}({}) mismatches {}({})".format(cq,
                                                                  cqh,
                                                                  oq,
                                                                  oqh)
    return True, no_mismatch_reason


class FingerprintSimiliarityCheck():

    def __init__(self, lhsxdebugfprint, rhsxdebugfprint, constant_oracle=lambda x: False, logger=None):
        self._lhsfprint = lhsxdebugfprint
        self._rhsfprint = rhsxdebugfprint
        self._url_similiar, self._url_reason = paqu_surjective_equal_p(lhsxdebugfprint._url,
                                                                       rhsxdebugfprint._url,
                                                                       constant_oracle=constant_oracle,
                                                                       logger=logger)
        self._queries_similiar, self._queries_reason = queries_surjective_equal_p(lhsxdebugfprint, rhsxdebugfprint, logger=logger)

    def get_result_summary(self):
        return "urls similiar: {} with reason {}\nqueries similiar: {} with reason {}".format(
            self._url_similiar,
            self._url_reason,
            self._queries_similiar,
            self._queries_reason)


def xdebug_fingerprints_equalp(fprintlhs, fprintrhs,
                               constant_oracle=lambda x: False, logger=None):
    checkResult = FingerprintSimiliarityCheck(fprintlhs, fprintrhs, constant_oracle=constant_oracle, logger=logger)
    logger.info(checkResult.get_result_summary())
    return (checkResult._url_similiar and checkResult._queries_similiar), checkResult


class FingerprintContainsQueryCheck():

    def __init__(self, refPaqu, refQuery, fingerprint, constant_oracle=lambda x: False, logger=None):
        self._refPaqu = refPaqu
        self._refQuery = refQuery
        self._fingerprint = fingerprint
        self._url_similiar, self._url_reason = paqu_surjective_equal_p(refPaqu,
                                                                       fingerprint._url,
                                                                       constant_oracle=constant_oracle,
                                                                       logger=logger)
        cqueries, waste = fingerprint._queries
        fqueryhashes = [sqlnorm.generate_normalized_query_hash(query)
                        for query in cqueries]
        refQueryHash = sqlnorm.generate_normalized_query_hash(refQuery)
        if logger is not None:
            logger.debug("refHash: {}".format(refQueryHash))
            for query, hsh in zip(cqueries, fqueryhashes):
                logger.debug("{} -> >{}<".format(hsh, query))
        if refQueryHash in fqueryhashes:
            self._contains_query = True
            self._contains_reason = "query found"
        else:
            self._contains_query = False
            self._contains_reason = "unable to find hash {} of query {}".format(refQueryHash, refQuery)

    def get_result_summary(self):
        return "urls similiar: {} with reason {}\ncontains query: {} with reason {}".format(self._url_similiar,
                                                                                            self._url_reason,
                                                                                            self._contains_query,
                                                                                            self._contains_reason)


def xdebug_fingerprint_has_query(refPaqu, refQuery, fingerprint, constant_oracle=lambda x: False, logger=None):
    checkResult = FingerprintContainsQueryCheck(refPaqu, refQuery, fingerprint, constant_oracle=constant_oracle,
                                                logger=logger)
    logger.info(checkResult.get_result_summary())
    return (checkResult._url_similiar and checkResult._contains_query), checkResult
