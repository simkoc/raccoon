#!/usr/bin/env python
import xdebugparser
import argparse
import sys


def drop_until_htdoc(path):
    arr = path.split("/")
    pos = arr.index("htdocs")
    return "/".join(arr[pos+1:])


def get_all_used_php_files(args):
    with open(args.file) as file:
        xdebug = xdebugparser.XdebugTrace(file)
        for php_file in xdebug.get_all_used_source_files():
            if args.relative:
                print "/{}".format(drop_until_htdoc(php_file))
            else:
                print "{}".format(php_file)


def parse_args(args):
    base_parser = argparse.ArgumentParser(description='the interface for the xdebug parser')

    subparsers = base_parser.add_subparsers()

    usedfiles = subparsers.add_parser("usedfiles",
                                      help="outputs all the used php files referenced in the passed xdebug")
    usedfiles.add_argument("file",
                           help="the xdebug file")
    usedfiles.add_argument("-r", "--relative",
                           dest="relative",
                           action="store_true",
                           help="output the files relative to the htdoc folder")
    usedfiles.set_defaults(func=get_all_used_php_files)

    return base_parser.parse_args(args)


def main(args):
    args_obj = parse_args(args)
    args_obj.func(args_obj)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
