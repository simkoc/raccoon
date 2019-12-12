import psycopg2 as postgres
import xdebugparser as xdebug
import zlib
import StringIO
import datetime


class race_suspect_short:

    def __init__(self, id, expid, refXdebug, chg_query, refpaqu,
                 projname, session, user):
        self._id = id
        self._expid = expid
        self._refXdebug = refXdebug
        self._query = chg_query
        self._refpaqu = refpaqu
        self._projname = projname
        self._session = session
        self._user = user


def get_connection(host, user, pwd, db_name):
    pars = {"database": db_name}

    if host:
        pars["host"] = host
    if user:
        pars["user"] = user
    if pwd:
        pars["password"] = pwd

    conn = postgres.connect(**pars)
    conn.autocommit = True
    return conn


def store_experiments(db_con, experiment, logger=None):
    query = """INSERT INTO ExperimentsView(projname,
                                           session,
                                           operation,
                                           username,
                                           ts,
                                           success,
                                           log1,
                                           log2)
                           SELECT %(projname)s,
                                  %(session)s,
                                  %(operation)s,
                                  %(username)s,
                                  %(ts)s,
                                  %(success)s,
                                  %(log1)s,
                                  %(log2)s
                           RETURNING id;"""

    with db_con.cursor() as cur:
        valuedict = {"projname": experiment._projname,
                     "session": experiment._session,
                     "operation": experiment._operation,
                     "username": experiment._username,
                     "ts": experiment._ts,
                     "success": experiment._success,
                     "log1": postgres.Binary(experiment.log1),
                     "log2": postgres.Binary(experiment.log2)}
        cur.execute(query, valuedict)
        return cur.fetchone()[0]

def get_experiment_logs(db_con, id, logger=None):
    query = """SELECT log1, log2
               FROM experimentsview
               WHERE id = %(id)s;"""
    valuedict = {"id": id}
    with db_con.cursor() as cur:
        cur.execute(query, valuedict)
        logs = cur.fetchall()[0]
        return zlib.decompress(logs[0]).splitlines(), zlib.decompress(logs[1]).splitlines()

def get_highest_experiment_id(db_con, logger=None):
    query = """SELECT MAX(id) FROM experimentsview;"""
    with db_con.cursor() as cur:
        cur.execute(query)
        return cur.fetchone()

def get_experiment_success(db_con, expid, logger=None):
    query ="""SELECT success FROM experimentsview WHERE id=%(id)s;"""
    with db_con.cursor() as cur:
        valuedict = {"id": expid}
        cur.execute(query, valuedict)
        return cur.fetchone()


def store_http_requests(db_con, request, logger=None):
        query = """INSERT INTO HTTPRequestsView(expid,
                                           selcmdctr,
                                           ts,
                                           url,
                                           method)
                           SELECT %(expid)s,
                                  %(selcmdctr)s,
                                  %(ts)s,
                                  %(url)s,
                                  %(method)s
                           RETURNING ctr;"""
        with db_con.cursor() as cur:
            valuedict = {"expid": request._expid,
                         "selcmdctr": request._selcmdctr,
                         "ts": request._ts,
                         "url": request._url,
                         "method": request._method}
            # print(query)
            # print(valuedict)
            cur.execute(query, valuedict)
            return cur.fetchone()[0]


def get_all_http_requests(db_con, expid, logger=None):
    query="""SELECT url, ts, selcmdctr, ctr FROM HTTPRequestsView where expid=%s ORDER BY ts;"""
    with db_con.cursor() as cur:
        cur.execute(query, (expid))
        return cur.fetchall()


def store_sel_commands(db_con, command, logger=None):
    query = """INSERT INTO SeleneseCommandsView(expid,
                                           tcname,
                                           command,
                                           target,
                                           value)
                           SELECT %(expid)s,
                                  %(tcname)s,
                                  %(command)s,
                                  %(target)s,
                                  %(value)s
                           RETURNING ctr;"""
    with db_con.cursor() as cur:
        valuedict = {"expid": command._expid,
                     "tcname": command._tcname,
                     "command": command._command,
                     "target": command._target,
                     "value": command._value}
        cur.execute(query, valuedict)
        return cur.fetchone()[0]


def store_xdebugs(db_con, xdebug, logger=None):
    query = """INSERT INTO XdebugDumpsRacoonView(expid,
                                           selcmdctr,
                                           httpreqctr,
                                           name,
                                           content)
                           SELECT %(expid)s,
                                  %(selcmdctr)s,
                                  %(httpreqctr)s,
                                  %(name)s,
                                  %(content)s"""
    with db_con.cursor() as cur:
        valuedict = {"expid": xdebug._expid,
                     "selcmdctr": xdebug._selcmdctr,
                     "httpreqctr": xdebug._httpreqctr,
                     "name": xdebug._name,
                     "content": postgres.Binary(xdebug._content)}
        cur.execute(query, valuedict)

def get_next_set_id(db_con):
    ms_query = """SELECT coalesce(max(set_id),-1) + 1 FROM RaceSuspectsView;"""
    with db_con.cursor() as cur:
        cur.execute(ms_query)
        ret = cur.fetchone()
        return ret[0]


def store_race_suspects(db_con, suspect, set_id, logger=None):
    query = """INSERT INTO RaceSuspectsView(set_id,
                                            sel_expid,
                                            sel_selcmdctr,
                                            sel_httpreqctr,
                                            sel_query,
                                            chg_expid,
                                            chg_selcmdctr,
                                            chg_httpreqctr,
                                            chg_query,
                                            timedelta)
                           SELECT %(set_id)s,
                                  %(sel_expid)s,
                                  %(sel_selcmdctr)s,
                                  %(sel_httpreqctr)s,
                                  %(sel_query)s,
                                  %(chg_expid)s,
                                  %(chg_selcmdctr)s,
                                  %(chg_httpreqctr)s,
                                  %(chg_query)s,
                                  %(timedelta)s
                           RETURNING id;"""

    with db_con.cursor() as cur:
        valuedict = {"set_id": set_id,
                     "sel_expid": suspect._select_request._expid,
                     "sel_selcmdctr": suspect._select_request._selcmdctr,
                     "sel_httpreqctr": suspect._select_request._httpreqctr,
                     "sel_query": suspect._select_query._query_string,
                     "chg_expid": suspect._change_request._expid,
                     "chg_selcmdctr": suspect._change_request._selcmdctr,
                     "chg_httpreqctr": suspect._change_request._httpreqctr,
                     "chg_query": suspect._change_query._query_string,
                     "timedelta": "{}".format(suspect.timedelta())}
        cur.execute(query, valuedict)
        return cur.fetchone()[0]


def retrieve_race_suspect(db_con, suspect_id, logger):
    suspect_query = """SELECT id,
                              chg_expid,
                              chg_selcmdctr,
                              chg_httpreqctr,
                              chg_query
                       FROM RaceSuspectsView
                       WHERE id = %(id)s;"""
    xdebug_query = """SELECT content,
                             name
                      FROM xdebugDumpsRacoonView
                      WHERE expid = %(expid)s AND
                            selcmdctr = %(selcmdctr)s AND
                            httpreqctr = %(httpreqctr)s;"""
    request_query = """SELECT url
                       FROM httprequestsview
                       WHERE ctr = %(httpreqctr)s AND
                             expid = %(expid)s AND
                             selcmdctr = %(selcmdctr)s;"""
    experiment_query = """SELECT projname,
                                 session,
                                 operation,
                                 username
                          FROM experimentsview
                          WHERE id = %(expid)s;"""

    with db_con.cursor() as cur:
        valuedict = {"id": suspect_id}
        cur.execute(suspect_query, valuedict)
        suspect_result = cur.fetchone()
        valuedict = {"expid": suspect_result[1],
                     "selcmdctr": suspect_result[2],
                     "httpreqctr": suspect_result[3]}
        logger.debug("valuedic xdebug query {}".format(valuedict))
        logger.debug("query {}".format(xdebug_query))
        cur.execute(xdebug_query, valuedict)
        xdebug_result = cur.fetchone()
        stream = StringIO.StringIO(zlib.decompress(xdebug_result[0]))
        x = xdebug.XdebugTrace(stream)
        cur.execute(request_query, valuedict)
        url_result = cur.fetchone()
        paqu = "/" + "/".join(url_result[0].split("/")[3:])
        cur.execute(experiment_query, valuedict)
        experiment_result = cur.fetchone()
        if len(x.get_sql_queries()) == 0:
            raise Exception("the retrieved race suspect reference xdebug does not contain any queries")
        return race_suspect_short(suspect_result[0],
                                  suspect_result[1],
                                  (x, xdebug_result[1]),  # I do not remember why I am doing a xtrace and paqu string pair here - legacy mb?
                                  suspect_result[4],
                                  paqu, experiment_result[0],
                                  "{}-{}".format(experiment_result[2], experiment_result[1]),
                                  experiment_result[3])


def enter_test_xdebugs(cur, testid, zips):
    xdebug_insert = """INSERT INTO TestXdebugsView (testid,
                                                    name,
                                                    content)
                                   VALUES ( %(testid)s,
                                            %(name)s,
                                            %(content)s);"""
    for zip in zips:
        valuedict = {"testid": testid,
                     "name": zip[1],
                     "content": postgres.Binary(zip[0])}
        cur.execute(xdebug_insert, valuedict)


def enter_race_test_results(db_con, race_suspect, success_count, zips, succs,
                            lssuccess_count, lpsuccess_count,
                            start_time, end_time, start_time_comp_ref, end_time_comp_ref,
                            start_time_testing, end_time_testing, start_time_eval,
                            end_time_eval, check_type):
    stimestamp = datetime.datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')
    etimestamp = datetime.datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S')
    refstimestamp = datetime.datetime.fromtimestamp(start_time_comp_ref).strftime('%Y-%m-%d %H:%M:%S')
    refetimestamp = datetime.datetime.fromtimestamp(end_time_comp_ref).strftime('%Y-%m-%d %H:%M:%S')
    teststimestamp = datetime.datetime.fromtimestamp(start_time_testing).strftime('%Y-%m-%d %H:%M:%S')
    testetimestamp = datetime.datetime.fromtimestamp(end_time_testing).strftime('%Y-%m-%d %H:%M:%S')
    evalstimestmap = datetime.datetime.fromtimestamp(start_time_eval).strftime('%Y-%m-%d %H:%M:%S')
    evaletimestmap = datetime.datetime.fromtimestamp(end_time_eval).strftime('%Y-%m-%d %H:%M:%S')
    test_insert = """INSERT INTO RaceTestsView (testedSuspect,
                                                ts,
                                                request_count,
                                                success_count,
                                                success_run_count,
                                                lssuccess_count,
                                                lpsuccess_count,
                                                start_time,
                                                end_time,
                                                start_time_comp_ref,
                                                end_time_comp_ref,
                                                start_time_testing,
                                                end_time_testing,
                                                start_time_eval,
                                                end_time_eval,
                                                check_type)
                                  VALUES ( %(suspectid)s,
                                           %(timestamp)s,
                                           10,
                                           %(sucesscount)s,
                                           %(succs)s,
                                           %(lssucesscount)s,
                                           %(lpsucesscount)s,
                                           %(start_time)s,
                                           %(end_time)s,
                                           %(start_time_comp_ref)s,
                                           %(end_time_comp_ref)s,
                                           %(start_time_testing)s,
                                           %(end_time_testing)s,
                                           %(start_time_eval)s,
                                           %(end_time_eval)s,
                                           %(check_type)s)
                                  RETURNING id;"""
    valuedict = {"suspectid": race_suspect._id,
                 "timestamp": datetime.datetime.now(),
                 "sucesscount": success_count,
                 "succs": succs,
                 "lssucesscount": lssuccess_count,
                 "lpsucesscount": lpsuccess_count,
                 "start_time": stimestamp,
                 "end_time": etimestamp,
                 "start_time_comp_ref": refstimestamp,
                 "end_time_comp_ref": refetimestamp,
                 "start_time_testing": teststimestamp,
                 "end_time_testing": testetimestamp,
                 "start_time_eval": evalstimestmap,
                 "end_time_eval": evaletimestmap,
                 "check_type": check_type}
    with db_con.cursor() as cur:
        cur.execute(test_insert, valuedict)
        testid = cur.fetchone()[0]
        enter_test_xdebugs(cur, testid, zips)

    return testid


def enter_litmus_test_results(db_con, experiment_id, success_run_count,
                              zips, sequentialp):
    insert_query = """INSERT INTO LitmusTestsView (experiment_id,
                                                   success_run_count,
                                                   type)
                                  VALUES ( %(experimentid)s,
                                           %(successruncount)s,
                                           %(type)s )
                                  RETURNING id;"""
    valuedict = {"experimentid": experiment_id,
                 "successruncount": success_run_count,
                 "type": "SEQUENTIAL" if sequentialp else "PARALLEL"}
    with db_con.cursor() as cur:
        cur.execute(insert_query, valuedict)
        testid = cur.fetchone()[0]
        enter_test_xdebugs(cur, testid, zips)

    return testid


def get_litmus_test_results(db_con, experiment_id, sequentialp):
    test_select_query = """SELECT id,
                                  success_run_count
                           FROM LitmusTestsView
                           WHERE experiment_id = %(experimentid)s AND
                                 type = %(type)s;"""
    xdebug_select_query = """SELECT name,
                                    content
                             FROM TestXdebugsView
                             WHERE testid = %(testid)s;"""
    valuedict = {"experimentid": experiment_id,
                 "type": "SEQUENTIAL" if sequentialp else "PARALLEL"}
    with db_con.cursor() as cur:
        cur.execute(test_select_query, valuedict)
        one = cur.fetchone()
        if one is not None:
            testid = one[0]
            success_run_count = one[1]
            valuedict = {"testid": testid}
            cur.execute(xdebug_select_query, valuedict)
            xdebugNamePairs = list()
            for record in cur:
                stream = StringIO.StringIO(zlib.decompress(record[1]))
                xdebugNamePairs.append((record[1], record[0], stream))
            return xdebugNamePairs, success_run_count
        else:
            return [], -1


def get_suspect_id_of_test(db_con, testid, logger=None):
    query = """SELECT testedsuspect
               FROM racetestsview
               WHERE id = %(testid)s;"""
    valuedict = {"testid": testid}
    with db_con.cursor() as cur:
        cur.execute(query, valuedict)
        one = cur.fetchone()
        return one[0]


def get_test_xdebugs(db_con, testid, logger=None):
    query = """SELECT content, name
               FROM testxdebugsview
               WHERE testid = %(testid)s;"""
    valuedict = {"testid": testid}
    with db_con.cursor() as cur:
        cur.execute(query, valuedict)
        xdebugNameTriples = list()
        for record in cur:
            stream = StringIO.StringIO(zlib.decompress(record[0]))
            xdebugNameTriples.append((record[0], record[1], stream))
        return xdebugNameTriples


class RaceTestResult:

    def __init__(self, wq, sq, lsucc, succ, exec_time):
        self.writing_query = wq
        self.reading_query = sq
        self.litmus_test_count = lsucc
        self.success_count = succ
        self.execution_time = exec_time

    def is_hit(self):
        return self.litmus_test_count < self.success_count

    def __str__(self):
        res = "%4s => lcount: %2d | succ: %2d | time: %s\n" % ("HIT" if self.is_hit() else "FAIL",
                                                               self.litmus_test_count,
                                                               self.success_count,
                                                               self.execution_time)
        res += self.writing_query
        res += "\n"
        res += self.reading_query

        return res


def get_race_test_results(db_con, expid, setid):
    query = """SELECT suspect.sel_query               AS rq,
                      suspect.chg_query               AS wq,
                      test.lssuccess_count            AS lsucc,
                      test.success_count              AS succ,
                      test.end_time - test.start_time AS exec_time
                FROM racesuspectsview AS suspect JOIN
                     racetestsview    AS test
                     ON suspect.id = test.testedsuspect
                WHERE suspect.sel_expid = %(expid)s AND
                      suspect.set_id    = %(setid)s;"""
    valuedict = {"expid": expid,
                 "setid": setid}
    with db_con.cursor() as cur:
        cur.execute(query, valuedict)
        ret = list()
        for record in cur:
            ret.append(RaceTestResult(record[0],
                                      record[1],
                                      record[2],
                                      record[3],
                                      record[4]))
        return ret


def get_experiment_set_ids(db_con, expid):
    query = """SELECT DISTINCT set_id
               FROM racesuspectsview
               WHERE sel_expid = %(expid)s;"""
    valuedict = {"expid": expid}
    with db_con.cursor() as cur:
        cur.execute(query, valuedict)
        ret = list()
        for record in cur:
            ret.append(record[0])
        return ret


def get_all_litmustest_xdebugs(db_con, expid):
    query = """SELECT content
               FROM TestXdebugsView AS txv JOIN
                    LitmusTestsView ON ltv ON txv.testid = ltv.id
               WHERE ltv.experiment_id = %(expid)s;"""
    valuedict = {"expid": expid}
    with db_con.cursor() as cur:
        cur.execute(query, valuedict)
        ret = list()
        for record in cur:
            ret.append(record[0])
        return ret


def get_all_experiment_ids(db_con, expid, set_id):
    query = """SELECT rtv.id
               FROM racesuspectsview AS rsv JOIN
                    racestestsview AS rtv ON rsv.id = rtv.testedsuspect
               WHERE rsv.sel_expid = %(expid)s AND
                     rsv.set_id = %(set_id)s;"""
    valuedict = {"expid": expid,
                 "set_id": set_id}
    with db_con.cursor() as cur:
        cur.execute(query, valuedict)
        ret = list()
        for record in cur:
            ret.append(record[0])
        return ret


def get_all_xdebugs(db_con, rt_id):
    pass

def get_xdebug_queries(db_con, expid):
    query = """SELECT selcmdctr, httpreqctr, content
               FROM XdebugDumpsRacoonView
               WHERE expid = expid;"""
    with db_con.cursor() as cur:
        cur.execute(query)
        data = cur.fetchall()
    
    return data
