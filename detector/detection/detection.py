"""
Author: Simon Koch <s9sikoch@stud.uni-saarland.de>
This file represents the main file for the automated
race condition detector and provides the facilities
to use deemon trace data for race vulnerability detection
"""
from dbinterface.postgres import get_all_sql_queries_of, Query, Request
from sqlanalysis.exceptions import ParserDebugException, SqlParserDoesNotParseThis, SqlParserDoesNotYetParseThis
from sqlanalysis.sqlanalyzer import SqlQuery
from sqlanalysis.sqlanalyzer_utest import TestAnalyzerUpdate, TestAnalyzerInsert, TestAnalyzerDelete
import unittest
import hashlib


_UNKNOWN_QUERIES_FILES = ".unknown_queries"


def convert_queries(queries, threshold, reduction_heuristic=True, logger=None, store_unknown=True):
    ret = []
    with open(_UNKNOWN_QUERIES_FILES, "a") as f:
        for query in queries:
            try:
                ret.append(Query(SqlQuery(query._content, logger), query._request, query._counter, query._time))
            except SqlParserDoesNotParseThis as e:
                pass
            except SqlParserDoesNotYetParseThis as e:
                # logger.error("query {} resulted in {}".format(query._content, e))
                if store_unknown:
                    f.write(query._content)
                    f.write("\n--\n")
            except Exception as e:
                logger.error("uncaught exeption {} for query '{}'".format(e, query._content))
                if store_unknown:
                    f.write(query._content)
                    f.write("\n--\n")
                raise
    ret = sorted(ret, key=lambda x: x._request, cmp=Request.request_smallerequal, reverse=True)
    if reduction_heuristic:
        # no_dups, req_count = remove_duplicate_query_request_pairs(ret)
        # print "request count is {}".format(req_count)
        # return remove_unlikely_queries(no_dups, req_count, threshold)
        return ret, []
    else:
        return ret, []


def remove_duplicate(re):
    if re != []:
        if re[0] in re[1:]:
            return remove_duplicate(re[1:])
        else:
            return [re[0]] + remove_duplicate(re[1:])
    else:
        return []


class InterdependencyHit():

    def __init__(self, select, change, select_request, change_request, select_counter, change_counter,
                 select_time, change_time):
        self._select_query = select
        self._change_query = change
        self._select_request = select_request
        self._change_request = change_request
        self._select_counter = select_counter
        self._change_counter = change_counter
        self._select_time = select_time
        self._change_time = change_time

    def timedelta(self):
        return self._change_time - self._select_time

    def __hash__(self):
        return int(hashlib.sha224(
            str(self._select_query.__hash__()) + str(self._change_query.__hash__())).hexdigest(),
                   16)

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __str__(self):
        return "Possible Interdependency Hit between request {}({}) and {}({})\n{}\n{}\n with timedelta {} using: {}".format(
            self._select_request,
            self._select_counter,
            self._change_request,
            self._change_counter,
            self._select_query._query_string,
            self._change_query._query_string,
            self._change_time - self._select_time,
            self._select_query.get_intersection(self._change_query))


def query_analyzation(queries, logger):
    logger.info("extracted {} queries from the given traces".format(len(queries)))
    hits = []
    for i in range(0, len(queries), 1):  # This is the sophisticated algorithm described in the paper
        try:
            q = queries[i]._content
            for j in range(i, -1, -1):
                p = queries[j]._content
                try:
                    intersection = []
                    if j != i and q._changing and not p._changing:  # ref issue #2
                        intersection = p.get_intersection(q)
                        # let's first only go for one-way
                        # rintersection = p.get_intersection_inv(q) + intersection
                        # rintersection = remove_duplicate(rintersection)
                    if len(intersection) > 0:
                        hit = InterdependencyHit(p, q, queries[j]._request, queries[i]._request,
                                                 queries[j]._counter, queries[i]._counter,
                                                 queries[j]._time, queries[i]._time)
                        hits.append(hit)
                except ParserDebugException as err:
                    print p
                    print q
                    print err
        except SqlParserDoesNotParseThis as err:
            logger.error("{}".format(err))
    return hits


def remove_non_vuln_hits(hits, threshold, logger=None):
    threshold = int(threshold)
    if threshold == -1:
        return hits, 0

    table = {}
    for hit in hits:
        if hit in table:
            # print "found one"
            table[hit] = table[hit] + 1
        else:
            table[hit] = 1

    rets = []
    delete_counter = 0

    for hit in hits:
        if table[hit] > threshold:
            delete_counter += 1
        else:
            rets.append(hit)

    return rets, delete_counter


def remove_non_unique_queries(queries, reference_expid_list, host, user, pwd, database,
                              non_state_changing=False, logger=None):  # non state changing NYI
    table = {}
    for uexpid in reference_expid_list:
        if logger is not None:
            logger.info("indexing queries of expid {}".format(uexpid))
        undesirables = get_all_sql_queries_of(uexpid, host, user, pwd, database, logger)
        for query in undesirables:
            table[query._content] = query._content
    ret = []
    delete_counter = 0
    logger.info("referencing extracted trace queries against previously indexed foreign trace queries")
    for query in queries:
        if query._content in table:
            delete_counter += 1
        else:
            ret.append(query)
    return ret, delete_counter


def parse_reference_expids(string):
    ret = []
    for expid in string.split(","):
        if expid == '':  # this is just in case given list is empty
            continue
        ret.append(int(expid))
    return ret


def inter_step_analyzation(args, logger):
    raise Exception("Not supported anymore")
    logger.info("starting analysis for expid {}".format(args.expid))
    queries = get_all_sql_queries_of(args.expid, args.host, args.user, args.pwd, args.database, logger)
    logger.info("got a total of {} queries".format(len(queries)))
    logger.debug("{}".format(queries))
    args.reference_expids = parse_reference_expids(args.reference_expids)
    queries, deleted = remove_non_unique_queries(queries, args.reference_expids,
                                                 args.host, args.user, args.pwd,
                                                 args.database, logger=logger,
                                                 non_state_changing=args.non_state_changing)
    logger.info("removed {} non trace unique queries".format(deleted))
    queries, stats = convert_queries(queries, float(args.threshold), logger=logger)
    logger.info("start analyzsation of queries")
    hits = query_analyzation(queries, logger)
    logger.info("remove unlikely hits")
    hits, delete_counter = remove_non_vuln_hits(hits, args.threshold, logger)
    logger.info("removed {} candidates above threshold".format(delete_counter))
    if args.order_by == "timedelta":
        hits = sorted(hits, key=lambda arg: arg.timedelta())
        hits = reversed(hits)
    for hit in hits:
        print hit
        print ""


def single_step_interleaving(expid, db_host, db_user, db_pwd, db_name,
                             rel_threshold=-1, order_by="timedelta", logger=None):
    if logger is not None:
        logger.debug("starting analysis for expid {}".format(expid))

    queries = get_all_sql_queries_of(expid, db_host, db_user, db_pwd, db_name, logger)

    if logger is not None:
        logger.debug("got a total of {} queries".format(len(queries)))
        for query in queries:
            logger.debug("{}".format(query))

    queries, stats = convert_queries(queries, 0, reduction_heuristic=False, logger=logger)

    def sort_into_requests(queries):
        table = {}
        for query in queries:
            if query._request in table:
                table[query._request].append(query)
            else:
                table[query._request] = [query]

        ret = []
        for key in sorted(list(table.keys()), reverse=True):
            ret.append(table[key])
        return ret

    if logger is not None:
        logger.debug("sorting queries into requests")

    request_hit_list = []

    for request_query_set in sort_into_requests(queries):
        if logger is not None:
            logger.info("analyzing request {}".format(request_query_set[0].request_string()))

        hits = query_analyzation(request_query_set, logger)
        hits, delete_counter = remove_non_vuln_hits(hits, rel_threshold, logger)
        if logger is not None:
            logger.info("removed {} candidates above threshold".format(delete_counter))
        if order_by == "timedelta":
            hits = sorted(hits, key=lambda arg: arg.timedelta())
            hits = hits[::-1]
        request_hit_list.append(hits)

    return request_hit_list


def test_interdependence(query_a, query_b, logger=None):
    query_a = SqlQuery(query_a)
    query_b = SqlQuery(query_b)
    print query_a
    print query_b
    intersection = query_a.get_intersection(query_b)
    if logger is not None:
        logger.info("QueryA {}".format(query_a))
        logger.info("QueryB {}".format(query_b))
    if len(intersection) > 1:
        print "Interdependent detected based on {}".format(intersection)
    else:
        print "given queries are not interdependent"


def run_unit_tests(type, logger):
    if type == "all" or type == "update":
        suite = unittest.TestLoader().loadTestsFromTestCase(TestAnalyzerUpdate)
        unittest.TextTestRunner(verbosity=2).run(suite)
    if type == "all" or type == "insert":
        suite = unittest.TestLoader().loadTestsFromTestCase(TestAnalyzerInsert)
        unittest.TextTestRunner(verbosity=2).run(suite)
    if type == "all" or type == "delete":
        suite = unittest.TestLoader().loadTestsFromTestCase(TestAnalyzerDelete)
        unittest.TextTestRunner(verbosity=2).run(suite)


def dump_all_queries(args, logger):
    logger.info("dumping all queries of expid {}".format(args.expid))
    for query in get_all_sql_queries_of(args.expid, args.host, args.user, args.pwd,
                                        args.database, logger):
        print query
