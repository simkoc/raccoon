#!/usr/bin/env python
"""
test
RRRRRR AAAAAAAAA CCCCCCCC OOOOOOOOOO OOOOOOOOO NN      N
R    R A       A C        O        O O       O N N     N
R    R A       A C        O        O O       O N  N    N
RRRRRR AAAAAAAAA C        O        O O       O N   N   N
RR     A       A C        O        O O       O N    N  N
R R    A       A C        O        O O       O N     N N
R  R   A       A C        O        O O       O N      NN
R   R  A       A CCCCCCCC OOOOOOOOOO OOOOOOOOO N       N
RAce COndition investigatiON
Author: Simon Koch <simon.koch@tu-braunschweig.de>
This file is the main program and wraps up the detection
as well as the test for sql based raceconditions in
webapps. It requires that the bitnami machine is set
up properly (using interceptor). Test
"""
import time
import sys
import argparse
import log
import paramiko as ssh
import database.postgres as db_interface
import xdebugparser as Xdebug
import os
import subprocess
from sets import Set
from os.path import expanduser
from detection.detection import single_step_interleaving
from testor.testor import run_simple_interleaving, run_litmus_test, STRICT_CHECK, RELAXED_CHECK
from testor.evaluation.evaluation import count_equalp_fingerprints, count_equalp_fingerprints_relaxed
from testor.evaluation.xdebug_fingerprinting import XdebugFingerprint, PaQu
from interceptor.hashQuery import generate_normalized_query_hash_ret
import py2neo
from vmHandling import RunningVirtualMachine
import cStringIO as StringIO
import zlib
import configparser
import time


REMOTE_INTERCEPT_SCRIPT_FILE_LOCATION = "/home/bitnami/mysql-proxy-0.8.5-linux-glibc2.3-x86-64bit/script.lua"
REMOTE_APACHE_ERROR_LOG = "/opt/bitnami/apache2/logs/error_log"
FIREBASE_GUNS = "10"
FIREBASE_LOG = "~/.racoon/firebases"
_CONST_TARGET_FOLDERS = ["/tmp/"]


def parse_args(args):
    parser = argparse.ArgumentParser(description='run parameters')
    parser.add_argument("--verbose",
                        dest="verbose",
                        action="store_true",
                        help="full debug print if flag is set")

    sub_parsers = parser.add_subparsers()

    # Deep Model parameter subparser
    # dm_parser = argparse.ArgumentParser(add_help=False)
    # dm_parser.add_argument("neohost",
    #                        help="the host of the deep model neo4j db")
    # dm_parser.add_argument("neouser",
    #                        help="the user of the deep model neo4j db")
    # dm_parser.add_argument("neopwd",
    #                        help="the password of the deep model neo4j db")

    # Postgres dbms parameter subparser
    db_parser = argparse.ArgumentParser(add_help=False)
    db_parser.add_argument("host", help="the ip of the dbms")
    db_parser.add_argument("user", help="the user of the database")
    db_parser.add_argument("pwd", help="the password of the user")
    db_parser.add_argument("database",
                           help="the database containing the traces/hits")
    db_parser.add_argument("--simulate",
                           dest="simulate",
                           action="store_true",
                           help="do not store results in database")

    # interleaving detection parameter subparser
    il_parser = argparse.ArgumentParser(add_help=False)
    il_parser.add_argument("threshold",
                           help="the maximum amount the same hit may appear before it is considered irrelevant (-1 for infinite)")
    il_parser.add_argument("expid",
                           help="the id of the trace to be analyzed")
    il_parser.set_defaults(non_state_changing="False")

    # Need another interleaving sub-parser without expid as argument... TODO: Find a better way to handle this one...
    threshold_parser = argparse.ArgumentParser(add_help=False)
    threshold_parser.add_argument("threshold",
                                  help="the maximum amount the same hit may appear before it is considered irrelevant (-1 for infinite)")
    threshold_parser.set_defaults(non_state_changing="False")

    # webapp basis parser
    wb_parser = argparse.ArgumentParser(add_help=False)

    wb_parser.add_argument("root_user",
                           help="the root user name of the vm")
    wb_parser.add_argument("root_pwd",
                           help="the password of the root user")
    wb_parser.add_argument("vm_ip",
                           help="the ip of the vm")
    wb_parser.add_argument("vm_name",
                           help="the name of the vm to run the test on")
    wb_parser.add_argument("vm_state",
                           help="the state in which to start the vm")

    # webapp testing
    wt_parser = argparse.ArgumentParser(add_help=False)
    # wt_parser.add_argument("vm_name",
    #                        help="the name of the vm")
    # wt_parser.add_argument("vm_state",
    #                        help="the name of the state to start the vm from")
    wt_parser.add_argument("max_fuse_delay",
                           help="timeout for entire selenese-receipe while runs towards firebases")
    wt_parser.add_argument("walzing_barrage_timer",
                           help="time between selenese-commands while runs towards firebases")
    wt_parser.add_argument("xpath",
                           help="the location of the xdebug files on the target machine")
    wt_parser.add_argument("racoon_path",
                           help="full path to racoon repository")
    wt_parser.add_argument("selenese_script_folder",
                           help="the selenese script to be tested")
    wt_parser.add_argument("hit_threshold",
                           help="the min number of parallel successfull requests to be considered a hit")
    wt_parser.add_argument("--relaxed-check",
                           dest="relaxed_check",
                           action="store_true",
                           help="relax the match checking to simply only look for the query itself")

    # further webapp parameters
    dg_parser = argparse.ArgumentParser(add_help=False)
    dg_parser.add_argument("proj_name",
                                help="name of project to be used in database")
    dg_parser.add_argument("operation",
                                help="operation executed on webapp")
    dg_parser.add_argument("web_user",
                                help="user name used in selenese receipe")
    dg_parser.add_argument("sel_runner",
                                help="full path to selenese.jar")
    dg_parser.add_argument("sel_timeout",
                                help="total timeout for selenese in ms")
    dg_parser.add_argument("sel_speed",
                                help="time between selenese commands in ms")
    dg_parser.add_argument("firefox",
                                help="full path to firefox")
    dg_parser.add_argument("sel_receipe",
                                help="full path to selenese receipe")

    # ground data gathering
    data_gathering = sub_parsers.add_parser("data_gathering",
                                            help="gather ground data needed for vulnerability detection",
                                            parents=[db_parser,
                                                     wb_parser,
                                                     dg_parser])
    data_gathering.set_defaults(func=ground_data_gathering)

    # just interleaving detection
    inl_parser = sub_parsers.add_parser("interleaving",
                                        help="just run the interleaving detection",
                                        parents=[db_parser,
                                                 il_parser])
    inl_parser.set_defaults(func=interleaving)

    # # just vulnerability testing
    # vuln_parser = sub_parsers.add_parser("vulnerability",
    #                                      help="just run the interleaving detection",
    #                                      parents=[db_parser,
    #                                               dm_parser,
    #                                               wt_parser])
    # vuln_parser.add_argument("suspect_id",
    #                          help="the db id of the hit to be tested")
    # vuln_parser.add_argument("--full-battery",
    #                          dest="full_battery",
    #                          action='store_true',
    #                          help="if set every interleaving hit associated with the trace of the id will be run")
    # vuln_parser.set_defaults(func=vulnerability)

    # executing test based on config file
    config_test = sub_parsers.add_parser("config",
                                         help="execute a test based on a config file (find example at racoon/example.conf)")
    config_test.add_argument("conf_file",
                             help="full path to config file")
    config_test.set_defaults(func=parse_conf)

    # full test
    full_test = sub_parsers.add_parser("full",
                                       help="analyze a trace and test all the resulting hits",
                                       parents=[db_parser,
                                                threshold_parser,
                                                wb_parser,
                                                wt_parser,
                                                dg_parser])
    full_test.set_defaults(func=full)

    # retesting
    single_suspect = sub_parsers.add_parser("single",
                                            help="tests a single racesuspect",
                                            parents=[db_parser,
                                                     wb_parser,
                                                     wt_parser])
    single_suspect.add_argument("suspectid",
                                help="the suspect id")
    single_suspect.set_defaults(func=single_suspect_test)

    # reeval
    reeval = sub_parsers.add_parser("reeval",
                                    help="reevaluate a captured result",
                                    parents=[db_parser])
    reeval.add_argument("testid",
                        help="the id of the test to be reevaluated")
    reeval.add_argument("expid",
                        help="the id of the experiment, the test is belonging to")
    reeval.add_argument("--relaxed-check",
                        dest="relaxed_check",
                        action="store_true",
                        help="relax the match checking to simply only look for the query itself")
    reeval.set_defaults(func=reeval_test_result)

    # show results
    results = sub_parsers.add_parser("results",
                                     help="show the results for a test case",
                                     parents=[db_parser])
    results.add_argument("expid",
                         help="the id of the testrun to showcase the results for")
    results.add_argument("--setid",
                         dest="setid",
                         help="the set id of to showcase - else last is chosen")
    results.add_argument("--full",
                         dest="full",
                         action="store_true",
                         help="whether to also show failed tests")
    results.set_defaults(func=show_results)

    # show raw queries
    queries = sub_parsers.add_parser("raw_queries",
                                     help="show all queries collected",
                                     parents=[db_parser])
    queries.add_argument("expid",
                         help="the id of the test to extract the queries from")
    queries.set_defaults(func=show_raw_queries)

    # to be a collection of analysis tools
    analysis = sub_parsers.add_parser("analysis",
                                      help="collection of analysis-tools",
                                      parents=[db_parser])
    analyis_sub_parser = analysis.add_subparsers()
    litmus_queries = analyis_sub_parser.add_parser("litmus-queries",
                                                    help="show queries from Xdebugs for given experiment")
    litmus_queries.add_argument("expid",
                                help="the id of the testrun to show the Xdebug queries of")
    litmus_queries.add_argument("-f",
                                dest="search_query",
                                help="optional search-query to be isolated from litmus-queries")
    litmus_queries.set_defaults(func=show_litmus_queries)

    return parser.parse_args(args)

def show_litmus_queries(pargs, logger=None):
    with db_interface.get_connection(pargs.host, pargs.user, pargs.pwd, pargs.database) as con:
        data = db_interface.get_xdebug_queries(con, pargs.expid)
        for selcmd in data:
            print "Queries for SELCMD " + str(selcmd[0]) + " and HTTPREQ " + str(selcmd[1]) + ":"
            try:
                stream = StringIO.StringIO(zlib.decompress(selcmd[2]))
                trace = Xdebug.XdebugTrace(stream)
                stream.close()
                queries = trace.get_sql_queries(keep_all_queries=True, logger=None)
                for element in queries:
                    for subelement in element:
                        if type(pargs.search_query) is str:
                            if subelement.find(pargs.search_query) != -1:
                                print subelement
                        else:
                            print subelement
            finally:
                stream.close()


def show_raw_queries(pargs, logger=None):
    pass


def extract_and_show_raw_queries(db_host, db_user, db_pwd, db_name, expid, logger=None):
    with db_interface.get_connection(db_host, db_user, db_pwd, db_name) as con:
        litmustest_xdebugs = db_interface.get_all_litmustest_xdebugs(con, expid)
        for xdebug in litmustest_xdebugs:
            xtrace, triple = XdebugTrace.XdebugTrace(xdebug)
            for query in xtrace.get_all_queries():
                print(triple)
                print(query)

        set_ids = db_interface.get_experiment_set_ids(con, expid)
        logger.info("available set ids are: {}".format(set_ids))
        setid = max(set_ids)
        logger.info("chosing max value: {}".format(setid))

        test_ids = db_interface.get_all_experiment_ids(con, expid, set_id)
        for id in test_ids:
            test_xdebugs = db_interface.get_all_xdebugs(con, id)
            for xdebug in test_xdebugs:
                xtrace, triple = XdebugTrace.XdebugTrace(xdebug)
                for query in xtrace.get_all_queries():
                    print(triple)
                    print(query)


def show_results(pargs, logger=None):
    logger.info("extracting results for {}".format(pargs.expid))
    extract_and_show_results(pargs.host, pargs.user, pargs.pwd, pargs.database,
                             pargs.expid, logger, show_all=pargs.full,
                             setid=(pargs.setid if pargs.setid is not None else None))


def extract_and_show_results(db_host, db_user, db_pwd, db_name, expid, logger,
                             show_all=False, setid=None):
    with db_interface.get_connection(db_host, db_user, db_pwd, db_name) as con:
        if setid is None:
            setids = db_interface.get_experiment_set_ids(con, expid)
            logger.info("available set ids are: {}".format(setids))
            if len(setids) == 0:
                logger.info("no stored information")
                return
            setid = max(setids)
            logger.info("chosing max value: {}".format(setid))

        race_test_results = db_interface.get_race_test_results(con, expid, setid)
        overall_test_amount = len(race_test_results)
        print("Absolute Test Count: %03d" % (overall_test_amount,))
        overall_test_time = float(sum([rtr.execution_time.total_seconds() for rtr in race_test_results])) / 60.0
        # count the amount of all tests
        # calculate the average test time per conducted test
        avgttime = [rtr for rtr in race_test_results if rtr.success_count != -1]
        if len(avgttime) == 0:
            avgttime = -1
        else:
            avgttime = (float(sum([rtr.execution_time.total_seconds() for rtr in avgttime])) / float(len(avgttime))) / 60.0
        counter = 1
        print(" Absolute Test Time: %03f min" % (overall_test_time,))
        print("  Average Test Time: %03f min" % (avgttime,))
        for result in race_test_results:
            if result.success_count != -1 or show_all:
                print("------------------(%03d)----------------------" % (counter,))
                print(result)
                logger.info(result)
                counter += 1

def ground_data_gathering(pargs, logger=None):
    success = subprocess.call(["../data_gathering/data_gathering.sh", pargs.host, pargs.user, pargs.pwd, pargs.database, pargs.proj_name, 
                    pargs.operation, pargs.web_user, pargs.vm_name, pargs.root_user, pargs.root_pwd, pargs.vm_state, pargs.vm_ip, 
                    pargs.sel_runner, pargs.sel_timeout, pargs.sel_speed, pargs.firefox, pargs.sel_receipe])
    if success != 0:
        logger.error("sel ran into issues")
        raise Exception()


def interleaving_single(expid, db_host, db_user, db_pwd, db_name,
                        logger, simulate=False):
    request_hits = single_step_interleaving(expid,
                                            db_host, db_user, db_pwd, db_name,
                                            logger=logger)

    # debug print if verbose
    for request in request_hits:
        for hit in request:
            logger.debug("{}".format(hit))

    ids = []
    if not simulate:
        logger.info("storing analysis results")
        with db_interface.get_connection(db_host, db_user,
                                         db_pwd, db_name) as con:
            set_id = db_interface.get_next_set_id(con)
            for request in request_hits:
                for hit in request:
                    ids.append(db_interface.store_race_suspects(con, hit, set_id))
    else:
        logger.info("no storing of results due to simulate flag being set")

    logger.debug("suspect ids: {}".format(ids))
    logger.info("stored {} suspects".format(len(ids)))

    return ids


def interleaving(pargs, logger=None):
    if logger is not None:
        logger.info("running interleaving analysis on trace {}".format(pargs.expid))
    interleaving_single(pargs.expid,
                        pargs.host, pargs.user, pargs.pwd, pargs.database,
                        simulate=pargs.simulate, logger=logger)


def get_apache_logs(user, ip, pwd, logger=None):
    if logger is not None:
        logger.info("retrieving apache error logs")
    client = ssh.SSHClient()
    client.set_missing_host_key_policy(ssh.AutoAddPolicy())
    try:
        client.connect(ip, username=user, password=pwd, look_for_keys=False,
                       allow_agent=False, timeout=5)
        with client.open_sftp() as ftp:
            file = ftp.file(REMOTE_APACHE_ERROR_LOG, "r")
            content = file.read()
            full_path = "{}/firebases/apache-log-{}.log".format(expanduser("~"),
                                                                time.time())
            with open(full_path, "w") as f:
                f.write(content)
    finally:
        client.close()


def set_query(user, ip, pwd, query, logger):
    # qhash = generate_normalized_query_hash_ret(query)
    # observed opencart voucher
    query = query.replace("`", "")  # ` is contained in xdebug but not in the send queries via proxy
    qhash = subprocess.check_output(["./interceptor/hashQuery.pex", query])
    logger.debug("connecting to {}@{} using {} setting query {}".format(user, ip, pwd, query))
    logger.info("the hash is set to: {}".format(qhash))
    client = ssh.SSHClient()
    client.set_missing_host_key_policy(ssh.AutoAddPolicy())
    try:
        client.connect(ip, username=user, password=pwd, look_for_keys=False,
                       allow_agent=False, timeout=5)
        command = "sed -i -e 's/local hoi = .*/local hoi = \\\"{}\\\"/g' {}".format(qhash,
                                                                                    REMOTE_INTERCEPT_SCRIPT_FILE_LOCATION)
        logger.debug(command)
        client.invoke_shell()
        stdin, stdout, stderr = client.exec_command(command)
        logger.info("{}\n{}".format(stdout.read(), stderr.read()))
    finally:
        client.close()


def get_litmus_test_results(experiment_id, db_host, db_user, db_pwd, db_name,
                            firebases, testcase, xpath, target, root_user,
                            root_password, vm_name, vm_state, logger=None,
                            sequentialp=True, do_not_run_tests=False):
    with db_interface.get_connection(db_host, db_user, db_pwd, db_name) as db_con:
        zipNameTriples, count = db_interface.get_litmus_test_results(db_con,
                                                                     experiment_id,
                                                                     sequentialp)
        if len(zipNameTriples) == 0:
            if do_not_run_tests:
                raise Exception("No {} litmustest found but running test forbidden".format("sequential" if sequentialp else "parallel"))
            logger.info("no stored {} litmus test results for experiment {} found. Generating them now.".format(
                "sequential" if sequentialp else "parallel",
                experiment_id))
            with RunningVirtualMachine(vm_name, vm_state, target, root_user, root_password, _CONST_TARGET_FOLDERS,
                                       logger=logger):
                set_query(root_user, target, root_password, "SELECT nothing FROM fake", logger)
                zipNameTriples, count = run_litmus_test(testcase, target, firebases,
                                                        root_user, root_password,
                                                        xpath, logger=logger,
                                                        sequentialp=sequentialp)
            db_interface.enter_litmus_test_results(db_con, experiment_id,
                                                   count, zipNameTriples,
                                                   sequentialp)
        else:
            logger.info("found {} litmus test results for experiment {}".format("sequential" if sequentialp else "parallel",
                                                                                experiment_id))

    xdebugFingerprints = list()
    for element in zipNameTriples:
        xdebug = Xdebug.XdebugTrace(element[2])
        # print xdebug
        xdebugFingerprints.append(XdebugFingerprint(xdebug, PaQu(element[1])))

    return xdebugFingerprints, count


def single_suspect_test(pargs, logger):
    firebases = []
    for counter in range(4040,4050):
        firebase = []
        firebase.append('127.0.0.1')
        firebase.append('%d' % counter)
        firebase.append(pargs.max_fuse_delay)
        firebase.append(pargs.walzing_barrage_timer)
        firebases.append(firebase)
    ids = [int(pargs.suspectid)]
    testcase_scripts = get_testcase_scripts(pargs.selenese_script_folder)
    with db_interface.get_connection(pargs.host, pargs.user, pargs.pwd, pargs.database) as db_con:
        suspect = db_interface.retrieve_race_suspect(db_con, pargs.suspectid, logger)
        expid = suspect._expid
    sequentialRefPrints, sequentialRunCount = get_litmus_test_results(expid,
                                                                      pargs.host,
                                                                      pargs.user,
                                                                      pargs.pwd,
                                                                      pargs.database,
                                                                      firebases,
                                                                      testcase_scripts,
                                                                      pargs.xpath,
                                                                      pargs.vm_ip,
                                                                      pargs.root_user,
                                                                      pargs.root_pwd,
                                                                      pargs.vm_name,
                                                                      pargs.vm_state,
                                                                      logger=logger,
                                                                      sequentialp=True)
    counter = 0
    for id in ids:
        check_type = RELAXED_CHECK if pargs.relaxed_check else STRICT_CHECK
        counter = counter + 1
        logger.info("running {}/{} of trace related race suspects".format(counter,
                                                                          len(ids)))
        vulnerability_single(id, pargs.host, pargs.user,
                             pargs.pwd, pargs.database,
                             firebases, testcase_scripts,
                             pargs.xpath, pargs.vm_ip, pargs.root_user,
                             pargs.root_pwd, pargs.vm_name, pargs.vm_state,
                             sequentialRefPrints, sequentialRunCount,
                             pargs.hit_threshold, expid,
                             logger=logger, check_type=check_type)


def vulnerability_single(suspect_id, db_host, db_user, db_pwd, db_name,
                         firebases, testcase_scripts, xpath,
                         target, root_user, root_password,
                         vm_name, vm_state,
                         sequentialRefPrints, sequentialRunCount,
                         hit_threshold, expid,
                         logger, check_type=STRICT_CHECK, dupl_set=Set()):
    start_time = time.time()

    logger.info("running vulnerability analysis of suspect {}".format(suspect_id))

    race_suspect = None
    with db_interface.get_connection(db_host, db_user,
                                     db_pwd, db_name) as db_con:
        race_suspect = db_interface.retrieve_race_suspect(db_con,
                                                          suspect_id,
                                                          logger)

    suspectFingerprint = XdebugFingerprint(race_suspect._refXdebug[0], PaQu(race_suspect._refpaqu))
    start_time_comp_ref = time.time()
    testp = False
    if check_type == STRICT_CHECK:
        seq_matches = count_equalp_fingerprints(suspectFingerprint,
                                                sequentialRefPrints,
                                                race_suspect._projname,
                                                race_suspect._session, race_suspect._user, 
                                                db_host, db_user, db_pwd, db_name, expid,
                                                logger=logger)
    elif check_type == RELAXED_CHECK:
        seq_matches = count_equalp_fingerprints_relaxed(suspectFingerprint,
                                                        race_suspect._query,
                                                        sequentialRefPrints,
                                                        race_suspect._projname,
                                                        race_suspect._session, race_suspect._user, 
                                                        db_host, db_user, db_pwd, db_name, expid,
                                                        logger=logger)
    else:
        raise Exception("Unknown testing function {}".format(check_type))

    if seq_matches >= sequentialRunCount:  # or seq_matches >= hit_threshold:
        logger.info("NOTE: candidate has {}/{}({}) matches with sequential litmus test. Interleaving test won't yield additional information".format(seq_matches,
                                                                                                                                                     sequentialRunCount,
                                                                                                                                                     hit_threshold))
        testp = False
    else:
        testp = True

    query = race_suspect._query.replace("`", "")
    qhash = subprocess.check_output(["./interceptor/hashQuery.pex", query])
    if qhash in dupl_set:
        logger.info("NOTE: we already ran an interleaving test on this changing query. Another test will just waste our time")
        testp = False
    else:
        dupl_set.add(qhash)

    end_time_comp_ref = time.time()
    start_time_testing = time.time()
    if testp:
        logger.info("running race condition test with query:\n {}".format(race_suspect._query))
        with RunningVirtualMachine(vm_name, vm_state, target, root_user, root_password, _CONST_TARGET_FOLDERS,
                                   logger=logger):
            set_query(root_user, target, root_password, race_suspect._query, logger)
            success_count, xzips, succ, time_list = run_simple_interleaving(testcase_scripts,
                                                                            target,
                                                                            firebases,
                                                                            root_user,
                                                                            root_password,
                                                                            xpath,
                                                                            race_suspect._refXdebug[0],
                                                                            race_suspect._refpaqu,
                                                                            race_suspect._query,
                                                                            race_suspect._projname,
                                                                            race_suspect._session,
                                                                            race_suspect._user,
                                                                            logger, db_host, 
                                                                            db_user, db_pwd, db_name, expid,
                                                                            hit_function=check_type)
            start_time_testing, end_time_testing, start_time_eval, end_time_eval = time_list
            get_apache_logs(root_user, target, root_password, logger)
    else:
        success_count = -1
        xzips = []
        succ = -1
        start_time_eval = time.time()
        end_time_eval = time.time()
        end_time_testing = time.time()

    testid = None
    with db_interface.get_connection(db_host, db_user,
                                     db_pwd, db_name) as db_con:
        end_time = time.time()
        testid = db_interface.enter_race_test_results(db_con, race_suspect,
                                                      success_count, xzips,
                                                      succ, seq_matches,
                                                      -1,  # removed parallel reference check
                                                      start_time,
                                                      end_time,
                                                      start_time_comp_ref,
                                                      end_time_comp_ref,
                                                      start_time_testing,
                                                      end_time_testing,
                                                      start_time_eval,
                                                      end_time_eval,
                                                      check_type)
        logger.info("inserted test result into database with id {}".format(testid))

    logger.info("forced interleaving check for suspect {} done.\n Results: {}/{}".format(suspect_id,
                                                                                         success_count,
                                                                                         succ))


def reeval_test_result(pargs, logger=None):
    race_suspect = None
    with db_interface.get_connection(pargs.host, pargs.user,
                                     pargs.pwd, pargs.database) as db_con:
        test_suspect = db_interface.get_suspect_id_of_test(db_con,
                                                           pargs.testid,
                                                           logger)
        race_suspect = db_interface.retrieve_race_suspect(db_con,
                                                          test_suspect,
                                                          logger)
        xdebugTriplets = db_interface.get_test_xdebugs(db_con, pargs.testid)

    suspectFingerprint = XdebugFingerprint(race_suspect._refXdebug[0], PaQu(race_suspect._refpaqu))

    fingerprints = list()
    for element in xdebugTriplets:
        xdebug = Xdebug.XdebugTrace(element[2])
        fingerprints.append(XdebugFingerprint(xdebug, PaQu(element[1])))

    if pargs.relaxed_check:
        count = count_equalp_fingerprints_relaxed(suspectFingerprint, race_suspect._query, fingerprints,
                                                  race_suspect._projname, race_suspect._session,
                                                  race_suspect._user, pargs.host, pargs.user, pargs.pwd, pargs.database, pargs.expid, logger=logger)
    else:
        count = count_equalp_fingerprints(suspectFingerprint, fingerprints, race_suspect._projname,
                                          race_suspect._session, race_suspect._user, pargs.host, pargs.user, pargs.pwd, pargs.database, pargs.expid, logger=logger)

    logger.info("overall {} hits".format(count))


def get_testcase_scripts(folder):
    recipes = ["{}/{}".format(folder, item) for item in os.listdir(folder) if os.path.isfile(os.path.join(folder, item)) and item[-1] != "~"]
    return recipes

def get_next_expid(pargs, logger=None):
    with db_interface.get_connection(pargs.host, pargs.user,
                                     pargs.pwd, pargs.database) as db_con:
        expid = db_interface.get_highest_experiment_id(db_con, logger)[0]
        if expid == None:
            expid = 1
        return expid

def start_firebases(racoon_path, walzing_barrage_timer, max_fuse_delay, logger=None):
    stop_script = racoon_path + "/detector/testor/distributedSelenese/kill-tmux-firebases.sh"
    logger.info("first stopping running firebases")
    subprocess.call([stop_script])
    script_path = racoon_path + "/detector/testor/distributedSelenese/start-single-firebase.sh"
    logger.info("starting firebase tmux sessions")
    
    firebases = []
    #walzing_barrage and max_fuse_delay
    for counter in range(4040,4050):
        if os.system("tmux ls | grep firebase-{}".format(str(counter)[3])) != 0:
            subprocess.call([script_path, str(counter), max_fuse_delay, walzing_barrage_timer])
            logger.info("firebase-{} started".format(str(counter)[3]))
        else:
            logger.info("firebase-{} already running".format(str(counter)[3]))
        firebase = []
        firebase.append('127.0.0.1')
        firebase.append('%d' % counter)
        firebase.append(max_fuse_delay)
        firebase.append(walzing_barrage_timer)
        firebases.append(firebase)
    return firebases

def parse_conf(pargs, logger=None):
    file_path = pargs.conf_file
    config = configparser.ConfigParser()
    config.read(file_path)
    parameters = parse_args
    parameters.__dict__ = dict(config.items("Parameters"))

    if config["Basis"]["action"] == "data_gathering":
        ground_data_gathering(parameters, logger=logger)
    elif config["Basis"]["action"] == "interleaving":
        interleaving(parameters, logger=logger)
    elif config["Basis"]["action"] == "full":
        full(parameters, logger=logger)
    elif config["Basis"]["action"] == "single":
        single_suspect_test(parameters, logger=logger)
    elif config["Basis"]["action"] == "reeval":
        reeval_test_result(parameters, logger=logger)
    elif config["Basis"]["action"] == "results":
        show_results(parameters, logger=logger)
    elif config["Basis"]["action"] == "raw_queries":
        show_raw_queries(elements, logger=logger)
    else:
        logger.error("no valid operation given in config file")

def full(pargs, logger=None):
    firebases = start_firebases(pargs.racoon_path, pargs.walzing_barrage_timer, pargs.max_fuse_delay, logger=logger)
    expid = get_next_expid(pargs, logger=logger)
    already_done = Set()
    ground_data_gathering(pargs, logger=logger)
    ids = interleaving_single(expid, pargs.host, pargs.user,
                              pargs.pwd, pargs.database, logger=logger)
    testcase_scripts = get_testcase_scripts(pargs.selenese_script_folder)
    logger.debug("using scripts {}".format(testcase_scripts))  # this can become a debug logging soon I hope
    sequentialRefPrints, sequentialRunCount = get_litmus_test_results(expid,
                                                                      pargs.host,
                                                                      pargs.user,
                                                                      pargs.pwd,
                                                                      pargs.database,
                                                                      firebases,
                                                                      testcase_scripts,
                                                                      pargs.xpath,
                                                                      pargs.vm_ip,
                                                                      pargs.root_user,
                                                                      pargs.root_pwd,
                                                                      pargs.vm_name,
                                                                      pargs.vm_state,
                                                                      logger=logger,
                                                                      sequentialp=True)
    counter = 0
    for id in ids:
        counter = counter + 1
        logger.info("running {}/{} of trace related race suspects".format(counter,
                                                                          len(ids)))
        vulnerability_single(id, pargs.host, pargs.user,
                             pargs.pwd, pargs.database,
                             firebases, testcase_scripts,
                             pargs.xpath, pargs.vm_ip, pargs.root_user,
                             pargs.root_pwd, pargs.vm_name, pargs.vm_state,
                             sequentialRefPrints, sequentialRunCount,
                             pargs.hit_threshold, expid,
                             logger=logger, check_type=RELAXED_CHECK if pargs.relaxed_check else STRICT_CHECK,
                             dupl_set=already_done)
    extract_and_show_results(pargs.host, pargs.user, pargs.pwd, pargs.database,
                             expid, logger)

def main(args):
    logger = log.getdebuglogger("racoon")
    pargs = parse_args(args)
    logger.info("config: {}".format(pargs))
    if pargs.verbose:
        logger.setLevel(log.LEVELS[2])
    else:
        logger.setLevel(log.LEVELS[0])
    pargs.func(pargs, logger)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
