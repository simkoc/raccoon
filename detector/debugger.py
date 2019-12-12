#!/usr/bin/env python

import argparse
import log
import sys
from detection.detection import dump_all_queries
from detection.dbinterface.postgres import get_raw_xdebug


def parse_args(args):
    parser = argparse.ArgumentParser(description='run parameters')
    parser.add_argument("--verbose",
                        dest="verbose",
                        action="store_true",
                        help="full debug print if flag is set")

    db_parser = argparse.ArgumentParser(add_help=False)
    db_parser.add_argument("host", help="the ip of the dbms")
    db_parser.add_argument("user", help="the user of the database")
    db_parser.add_argument("pwd", help="the password of the user")
    db_parser.add_argument("database",
                           help="the database containing the traces/hits")

    sub_parsers = parser.add_subparsers()

    show_queries = sub_parsers.add_parser("queries",
                                          parents=[db_parser],
                                          help="shows all the queries belonging to a single request")
    show_queries.add_argument("expid",
                              help="the experiment id")
    show_queries.add_argument("selctr",
                              help="the counter for the selenese command")
    show_queries.add_argument("reqctr",
                              help="the counter for the http request")
    show_queries.set_defaults(func=show_all_contained_queries)

    show_xdebug = sub_parsers.add_parser("raw_xdebug",
                                         parents=[db_parser],
                                         help="shows all the queries belonging to a single request")
    show_xdebug.add_argument("expid",
                             help="the experiment id")
    show_xdebug.add_argument("selctr",
                             help="the counter for the selenese command")
    show_xdebug.add_argument("reqctr",
                             help="the counter for the http request")
    show_xdebug.set_defaults(func=show_raw_xdebug)

    return parser.parse_args(args)


def show_all_contained_queries(pargs, logger):
    dump_all_queries(pargs, logger)


def show_raw_xdebug(pargs, logger):
    string = get_raw_xdebug(pargs.expid, pargs.selctr, pargs.reqctr,
                            pargs.user, pargs.pwd, pargs.host, pargs.database,
                            logger)
    print(string)

    
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
