"""
Author: Simon Koch <s9sikoch@stud.uni-saarland.de>
This file provides the facilities to access the
relevant database(s) containing the SQL queries
of interest.
"""
import psycopg2 as psql
import xdebugparser as xpar
import cStringIO as StringIO
import zlib
import hashlib
import re
import datetime


def sanitize_query(query_string): # who though that a sanitaziation here is at all smart?
    # print query_string
    # query = re.sub(r"^[ ]*'", "", query_string)
    # query = re.sub(r"'[ ]*$", "", query)
    # query = re.sub(r"`", "", query)
    return query_string


class Request():
    def __init__(self, expid, selcmdctr, httpreqctr):
        self._expid = expid
        self._selcmdctr = selcmdctr
        self._httpreqctr = httpreqctr

    def __hash__(self):
        return int(hashlib.sha224(self.__str__()).hexdigest(), 16)

    def __str__(self):
        return "{}-{}-{}".format(self._expid, self._selcmdctr, self._httpreqctr)

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    @staticmethod
    def request_smallerequal(request_lhs, request_rhs):
        if request_lhs._expid < request_rhs._expid:
            return True
        elif request_lhs._expid == request_rhs._expid:
            if request_lhs._selcmdctr < request_rhs._selcmdctr:
                return True
            elif request_lhs._selcmdctr == request_rhs._selcmdctr:
                if request_lhs._httpreqctr <= request_rhs._httpreqctr:
                    return True
                else:
                    return False
            return False
        return False


class Query():
    def __init__(self, content, request, counter, time):
        self._content = content
        self._request = request
        self._counter = counter
        self._time = time

    def __str__(self):
        return "[{}({})] {}".format(self._request, self._counter, self._content)

    def __repr__(self):
        return self.__str__()

    def request_string(self):
        return self._request.__str__()


def get_raw_xdebug(expid, selcmdctr, httpreqctr, user, pwd, host, database, logger):
    with psql.connect(host=host, user=user, password=pwd, database=database) as con:
        with con.cursor() as cur:
            query = """SELECT
                             content
                       FROM
                             XdebugDumpsView
                       WHERE
                             expid = %s AND
                             selcmdctr = %s AND
                             httpreqctr = %s
                       ORDER BY
                             expid, selcmdctr, httpreqctr ASC;"""
            cur.execute(query, (expid, selcmdctr, httpreqctr, ))
            res = cur.fetchall()
            assert len(res) == 1, "there are {} instead of 1 xdebug".format(len(res))
            res = res[0]
            string = zlib.decompress(res[0])
            return string


def get_all_sql_queries_of(expid, host, user, pwd, database, logger):
    with psql.connect(host=host, user=user, password=pwd, database=database) as con:
        with con.cursor() as cur:
            query = """SELECT
                             expid,selcmdctr,httpreqctr,content
                       FROM
                             XdebugDumpsView
                       WHERE
                             expid = %s
                       ORDER BY
                             expid, selcmdctr, httpreqctr ASC;"""
            cur.execute(query, (expid,))
            queries = []
            # logger.debug("I have currently {} queries in storage".format(len(queries)))
            for xdebug in cur.fetchall():
                logger.info("extracting query from expid {} selcmdctr {} httpreqctr {}".format(
                    expid, xdebug[1], xdebug[2]))
                try:
                    stream = None
                    stream = StringIO.StringIO(zlib.decompress(xdebug[3]))
                    trace = None
                    trace = xpar.XdebugTrace(stream)
                    stream.close()
                    quers = []
                    quers, offsets = trace.get_sql_queries(keep_all_queries=True, logger=None)
                    logger.debug("raw queries: {}".format(quers))
                    counter = 0
                    for query, offset in zip(quers, offsets):
                        try:
                            time = trace._time + datetime.timedelta(seconds=float(offset))
                            queries.append(Query(sanitize_query(query),
                                                 Request(xdebug[0], xdebug[1], xdebug[2]),
                                                 counter,
                                                 time))
                            counter += 1
                        except Exception as err:
                            logger.error("related query: {}".format(sanitize_query(query)))
                            logger.error("{}".format(err))
                            with open("/home/simkoc/tmp/xdebug_offender.xt", 'w') as f:
                                f.write(zlib.decompress(xdebug[3]))
                                logger.error(
                                    "dumped violating xdebug into ~/tmp/xdebug_offender.xt")
                            raise
                finally:
                    stream.close()
            return queries
