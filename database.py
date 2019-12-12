#!/usr/bin/env python

import argparse
import json
from detector.database.postgres import get_connection, store_experiments, store_sel_commands, get_highest_experiment_id, store_http_requests, store_xdebugs, get_all_http_requests, get_experiment_logs
from os.path import expanduser
import zlib


GROUND_DATA_LOG_PATH = expanduser("~") + "/.racoon/data/data_gathering/logs/ground_data_log"
A_LOG_1_PATH = expanduser("~") + "/.racoon/data/data_gathering/logs/apache_log_1"
A_LOG_2_PATH = expanduser("~") + "/.racoon/data/data_gathering/logs/apache_log_2"
XDEBUGS_LIST_PATH = expanduser("~") + "/.racoon/data/data_gathering/xdebugs.list"
XDEBUGS_PATH = expanduser("~") + "/.racoon/data/data_gathering/xdebugs/"


parser = argparse.ArgumentParser()
parser.add_argument('db_host', type=str)
parser.add_argument('db_user', type=str)
parser.add_argument('db_pwd', type=str)
parser.add_argument('db_name', type=str)
parser.add_argument('projname', type=str)
parser.add_argument('session', type=str)
parser.add_argument('operation', type=str)
parser.add_argument('username', type=str)
parser.add_argument('sel_delay', type=int)
parser.add_argument('ts', type=str)
parser.add_argument('success', type=str)
parser.add_argument('selpath', type=str)
parser.add_argument('url', type=str)


args = parser.parse_args()


class experiments:
    def __init__(self, projname, session, operation, username, ts, success, log1_path, log2_path):
        self._projname = str(projname)
        self._session = str(session)
        self._operation = str(operation)
        self._username = str(username)
        self._ts = ts
        self._success = success
        self.log1 = zlib.compress(open(log1_path).read())
        self.log2 = zlib.compress(open(log2_path).read())


class commands:
    def __init__(self, expid, tcname, command, target, value):
        self._expid = int(expid)
        self._tcname = str(tcname)
        self._command = str(command)
        self._target = str(target)
        self._value = str(value)


class requests:
    def __init__(self, expid, selcmdctr, ts, url, method):
        self._expid = expid
        self._selcmdctr = int(selcmdctr)
        self._ts = ts
        self._url = str(url)
        self._method = str(method)


class xdebugs:
    def __init__(self, expid, selcmdctr, httpreqctr, name, xpath):
        self._expid = expid
        self._selcmdctr = int(selcmdctr)
        self._httpreqctr = int(httpreqctr)
        self._name = str(name)
        self._content = zlib.compress(open(xpath).read())


# connect to database
con = get_connection(args.db_host, args.db_user, args.db_pwd, args.db_name)


# actual insertion in database
def create_experiment(projname, session, operation, username, ts, success, log1_path, log2_path):
    experiment = experiments(projname, session,
                             operation, username, ts, success, log1_path, log2_path)
    return store_experiments(con, experiment)

def create_sel_command(expid, tcname, command, target, value):
    command = commands(expid, tcname, command, target, value)
    store_sel_commands(con, command)


def create_http_request(expid, selcmdctr, ts, url, method):
    request = requests(expid, selcmdctr, ts, url, method)
    store_http_requests(con, request)


def create_xdebug(expid, selcmdctr, httpreqctr, name, xpath):
    xdebug = xdebugs(expid, selcmdctr, httpreqctr, name, xpath)
    store_xdebugs(con, xdebug)


# gaining data of selenese-commands
def get_testcase_name(tc_path):
    with open(tc_path) as f:
        content = f.readlines()

    # find title of recipe
    for line in content:
        if "<title>" in line:
            title = line[7:len(line)-9]
    return title


def get_testcase_values(tc_path):
    with open(tc_path) as f:
        content = f.readlines()

    values = []
    # put commands in array
    for line in content:
        if "<td>" in line and "</td>" in line and not "<tr>" in line and not "</tr>" in line:
            values.append(line[line.find("<td>") + 4:len(line)-6])
    return values


def parse_test_case(exp_id, tc_path):
    ttype = tc_path.split(".")[-1]
    if ttype == "html":
        selcmd_to_database_html(exp_id, tc_path)
    else:
        selcmd_to_database_json(exp_id, tc_path)


def selcmd_to_database_json(exp_id, tc_path):
    with open(tc_path) as f:
        sel = json.load(f)
        tc_name = sel['name']
        values = list()
        for com in sel['tests'][0]['commands']:
            command = com['command']
            target = com['target']
            value = com['value']
            values += [command, target, value]
        i = 0
        for count in range(0, len(values), 3):
            i += 1
            print("{}-{}-{}".format(values[count], values[count+1], values[count+2]))
            create_sel_command(exp_id, tc_name,
                               values[count], values[count+1], values[count+2])

    
def selcmd_to_database_html(exp_id, tc_path):
    values = get_testcase_values(tc_path)
    tc_name = get_testcase_name(tc_path)
    # NOTE: besser die standard range function verwenden
    # why steps of 3
    i = 0
    for count in range(0, len(values), 3):
        i += 1
        create_sel_command(exp_id, tc_name,
                           values[count], values[count+1], values[count+2])


# gaining data of http-requests
def http_requests_to_database(exp_id):
    with open(GROUND_DATA_LOG_PATH) as f:
        log = f.readlines()

    content = []

    # drop unrelevant lines (i.e. lines not representing a request to a php file)
    for line in log:
        if line.find(".php", 0, len(line)-1) == -1 and line.find(" / ", 29, len(line)-1) == -1:
            line = ""
        if line != "":
            content.append(line)

    start_time = int(content[0][13:15])*3600 + int(content[0][16:18])*60 + int(content[0][19:21])

    # setting urls to categories
    selcmd_cat_url = []

    for i in range(0, len(content)):
        time = int(content[i][13:15])*3600 + int(content[i][16:18])*60 + int(content[i][19:21])
        step = int(round((time - start_time)*1000.0/args.sel_delay))
        if step == 0:
            step = 1
        while len(selcmd_cat_url) -1 < step:
            selcmd_cat_url.append([])
        if "GET" in content[i]:
            selcmd_cat_url[step].append(args.url + content[i][33:content[i].find("HTTP/1.1")-1])
        else:
            selcmd_cat_url[step].append(args.url + content[i][34:content[i].find("HTTP/1.1")-1])

    # setting ts to categories
    selcmd_cat_ts = []

    for i in range(0, len(content)):
        time = int(content[i][13:15])*3600 + int(content[i][16:18])*60 + int(content[i][19:21])
        step = int(round((time - start_time)*1000.0/args.sel_delay))
        if step == 0:
            step = 1
        while len(selcmd_cat_ts) -1 < step:
            selcmd_cat_ts.append([])
        selcmd_cat_ts.append([])
        selcmd_cat_ts[step].append(content[i][1:20])

    # setting method to categories
    selcmd_cat_method = []

    for i in range(0, len(content)):
        time = int(content[i][13:15])*3600 + int(content[i][16:18])*60 + int(content[i][19:21])
        step = int(round((time - start_time)*1000.0/args.sel_delay))
        if step == 0:
            step = 1
        while len(selcmd_cat_method) -1 < step:
            selcmd_cat_method.append([])
        if "GET" in content[i]:
            selcmd_cat_method[step].append(content[i][29:32])
        else:
            selcmd_cat_method[step].append(content[i][29:33])

    # todo: this loop goes one over the limit :/ and thus violates the foreign key constraints
    for i in range(len(selcmd_cat_method)):
        for j in range(len(selcmd_cat_method[i])):
            create_http_request(exp_id, i, selcmd_cat_ts[i][j],
                                selcmd_cat_url[i][j], selcmd_cat_method[i][j])

# gaining data of xdebugs
def xdebugs_to_database():
        with open(XDEBUGS_LIST_PATH) as f:
            xdebugs = f.readlines()

        details = []
        for line in xdebugs:
            xdebug = line[0:len(line)-1]
            with open(xdebug) as f:
                lines = f.readlines()
            for line in lines:
                if "TRACE START" in line:
                    trace_start = line[13:len(line)-2]
                    trace_start = trace_start[11:len(trace_start)]
                    trace_start = int(trace_start[0:2]) * 3600 + int(trace_start[3:5]) * 60 + int(trace_start[6:8])
                xdebug = xdebug[xdebug.find("xdebug."):len(xdebug)]

            transfer = []
            transfer.append(trace_start)
            transfer.append(xdebug)
            details.append(transfer)

        # sort xdebug_list by timestamps
        details.sort()
        
        # get http_requests for given expid -- [0] = url [1] = timestamp [2] = selcmdctr [3] = httpreqctr
        http_req = get_all_http_requests(con, get_highest_experiment_id(con))

        # format httprequest urls and time and copy it to string/int list
        http_req_string = []
        for line in http_req:
            url = line[0]
            url = url[22:len(url)]
            if url == "/":
                url = "/."
            url = url.replace("index.php", ".index.php")
            url = url[1:len(url)]
            url = url.replace('.', '_').replace('?', '_').replace('/', '_').replace('&', '_')

            time = line[1].strftime("%H:%M:%S")
            time = int(time[0:2]) * 3600 + int(time[3:5]) * 60 + int(time[6:8])

            transfer_list = []
            transfer_list.append(time)
            transfer_list.append(url)
            transfer_list.append(int(line[2]))
            transfer_list.append(int(line[3]))
            http_req_string.append(transfer_list)

        # sort the list by timestamps
        http_req_string.sort()

        # connect xdebugs to httprequests
        for i in range(0, len(details)):
            if details[i] != "empty":
                for j in range(0, len(http_req_string)):
                    if http_req_string[j] != "empty":
                        start = details[i][1].find(".")
                        end = details[i][1][start+1:len(details[i][1])].find(".") + start + 1
                
                        # create xdebug entry in database
                        if http_req_string[j][1] in details[i][1][start:end]:
                            create_xdebug(get_highest_experiment_id(con), http_req_string[j][2],
                                          http_req_string[j][3], details[i][1], XDEBUGS_PATH+details[i][1])
                            create_xdebug
                            details[i] = "empty"
                            http_req_string[j] = "empty"


# start the show
exp_id = create_experiment(args.projname, args.session, args.operation,
                           args.username, args.ts, args.success, A_LOG_1_PATH, A_LOG_2_PATH)
parse_test_case(exp_id, args.selpath)
http_requests_to_database(exp_id)
xdebugs_to_database()