#!/usr/bin/python

import argparse
from dateutil.parser import parse
import detector.database.postgres as db
import StringIO
import zlib
import sys

parser = argparse.ArgumentParser()
parser.add_argument('db_host', type=str)
parser.add_argument('db_user', type=str)
parser.add_argument('db_pwd', type=str)
parser.add_argument('db_name', type=str)
parser.add_argument('experiment', type=str)


def get_oracle_trace_start_end_time(con, exp_id):
    query = """SELECT content
               FROM XdebugDumpsRacoonView
               WHERE expid = %(expid)s"""
    dic = {"expid": exp_id}
    minimum = parse('2100-01-01 00:00:00')
    maximum = parse('1992-03-20 00:00:00')
    with con.cursor() as cur:
        cur.execute(query, dic)
        for record in cur:
            stream = StringIO.StringIO(zlib.decompress(record[0]))
            stream.readline()
            stream.readline()
            start = stream.readline()
            assert(start[0:11] == 'TRACE START')
            time = parse(start[13:-2])
            if time > maximum:
                maximum = time
            elif time < minimum:
                minimum = time
    return minimum, maximum


def get_litmus_trace_start_end_time(con, exp_id):
    query = """SELECT id
               FROM litmustests
               WHERE experiment_id = %(expid)s"""
    dic = {"expid": exp_id}
    litmus_id = -1
    with con.cursor() as cur:
        cur.execute(query, dic)
        litmus_id = cur.fetchone()[0]
    query = """SELECT content
               FROM TestXdebugsView
               WHERE testid = %(testid)s"""
    dic = {"testid": litmus_id}
    minimum = parse('2100-01-01 00:00:00')
    maximum = parse('1992-03-20 00:00:00')
    with con.cursor() as cur:
        cur.execute(query, dic)
        for record in cur:
            stream = StringIO.StringIO(zlib.decompress(record[0]))
            stream.readline()
            stream.readline()
            start = stream.readline()
            assert(start[0:11] == 'TRACE START')
            time = parse(start[13:-2])
            if time > maximum:
                maximum = time
            elif time < minimum:
                minimum = time
    return minimum, maximum


def main(args):
    pargs = parser.parse_args(args)
    with db.get_connection(pargs.db_host, pargs.db_user,
                           pargs.db_pwd, pargs.db_name) as con:
        oracle_start, oracle_end = get_oracle_trace_start_end_time(con, pargs.experiment)
        litmus_start, litmus_end = get_litmus_trace_start_end_time(con, pargs.experiment)
        print("Oracle Run Times")
        print("{} -> {}".format(oracle_start, oracle_end))
        print("Litmus Test Run Times")
        print("{} -> {}".format(litmus_start, litmus_end))


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
