#!/usr/bin/env python

import argparse
import log
import sys


def parse_args(args):
    parser = argparse.ArgumentParser(description='detection parameters')

    sub_parsers = parser.add_subparsers()

    # Postgres dbms paramter subparser #
    database_parameter_parser = argparse.ArgumentParser(add_help=False)
    database_parameter_parser.add_argument("host", help="the host ip of the dbms")
    database_parameter_parser.add_argument("user", help="the user of the database")
    database_parameter_parser.add_argument("pwd", help="the password of the user")
    database_parameter_parser.add_argument("database", help="the name of the database")

    analysis_shared_parameter_parser = argparse.ArgumentParser(add_help=False)
    analysis_shared_parameter_parser.add_argument("threshold",
                                                  help="\
the maximum amount the same hit may appear before it is considered irrelevant (-1 for infinite)")
    analysis_shared_parameter_parser.add_argument("reference_expids",
                                                  help="\
a list of experiment ids to reference out not trace unique queries")
    analysis_shared_parameter_parser.add_argument("expid",
                                                  help="the id of the trace to be analyzed")
    analysis_shared_parameter_parser.add_argument("--non-state-changing", dest="non_state_changing",
                                                  help="\
also apply the not-unique reduction to non state changing queries (NYI)")
    analysis_shared_parameter_parser.add_argument("--order-by",
                                                  dest="order_by",
                                                  help="\
                                                  to order by which attribute {timedelta, order}",
                                                  default="order")
    analysis_shared_parameter_parser.set_defaults(non_state_changing="False")
    # Interdependency Analysis #
    interdep_main_parser = sub_parsers.add_parser("interdependency",
                                                  help="\
extract all the queries from the given trace and dump them into a file")
    interdep_parser = interdep_main_parser.add_subparsers()

    # Full Trace Interdependency Analysis #
    interdep_inter = interdep_parser.add_parser("interStep", help="check four interdependencies in the full trace",
                                                parents=[database_parameter_parser,
                                                         analysis_shared_parameter_parser])
    interdep_inter.set_defaults(func=inter_step_analyzation)

    # Step By Step Interdependency Analysis #
    interdep_inter = interdep_parser.add_parser("singleStep", help="check four interdependencies in the full trace",
                                                parents=[database_parameter_parser,
                                                         analysis_shared_parameter_parser])
    interdep_inter.set_defaults(func=single_step_analyzation)

    # Test Two Queries For Interdependency #
    strace_query_testing = sub_parsers.add_parser("test",
                                                  help="debug mode to test if two queries are interdependent")
    strace_query_testing.add_argument("query_a", help="the first query to test interdependence with")
    strace_query_testing.add_argument("query_b", help="the second query to test interdependence with")
    strace_query_testing.set_defaults(func=test_interdependence)

    # Run UnitTest test suite
    selfcheck = sub_parsers.add_parser("selfcheck",
                                       help="calling this runs the unit test suite")
    selfcheck .add_argument("--type",
                            dest="type",
                            help="which test suite to run {all,insert,update,select,delete}",
                            default="all")
    selfcheck.set_defaults(func=run_unit_tests)

    # Dump all queries of trace
    dump_queries = sub_parsers.add_parser("dump_queries",
                                          help="dump all queries of a given expid",
                                          parents=[database_parameter_parser])
    dump_queries.add_argument("expid",
                              help="the expid of the trace to dump all queries from")
    dump_queries.set_defaults(func=dump_all_queries)

    return parser.parse_args(args)


def main(args):
    logger = log.getdebuglogger("detector")

    args_obj = parse_args(args)
    # print "'{}'".format(int(args_obj.threshold))

    args_obj.func(args_obj, logger)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
