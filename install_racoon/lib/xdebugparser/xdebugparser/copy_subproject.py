#!/usr/bin/env python
import xdebugparser
import argparse
import sys
from os.path import exists
from os import makedirs
from shutil import copyfile, rmtree


def drop_until_htdoc(fpath):
    arr = fpath.split("/")
    pos = arr.index("htdocs")
    return "/".join(arr[pos+1:])


def create_folders(folders, base_folder):
    sub_folder = base_folder
    for folder in folders:
        sub_folder = "{}/{}".format(sub_folder, folder)
        if not exists(sub_folder):
            makedirs(sub_folder)


def copy_file_with_path_structure(fpath, base_folder):
    arr = fpath.split("/")
    pos = arr.index("htdocs")
    create_folders(arr[pos+1:-1], base_folder)
    final = "{}/{}".format(base_folder, "/".join(arr[pos+1:]))
    copyfile(fpath, final)
    return final


def copy_all_used_php_files(args):
    if exists(args.target):
        if args.force:
            rmtree(args.target)
            makedirs(args.target)
        else:
            raise Exception("target folder already exists")
    else:
        makedirs(args.target)

    with open(args.file) as file:
        xdebug = xdebugparser.XdebugTrace(file)
        for php_file in xdebug.get_all_used_source_files():
            php_file = "{}/{}".format(args.source, drop_until_htdoc(php_file))
            final = copy_file_with_path_structure(php_file, args.target)
            print "copy {} to {}".format(php_file, final)


def parse_args(args):
    base_parser = argparse.ArgumentParser(
        description='the interface for the xdebug parser')

    base_parser.add_argument("file",
                           help="the xdebug file")
    base_parser.add_argument("source",
                             help="the source folder for copying the relevant files")
    base_parser.add_argument("target",
                           help="the folder into which to copy the relevant files")
    base_parser.add_argument("-f", "--force",
                             dest="force",
                             action="store_true",
                             help="if target folder exists, supersede")
    base_parser.set_defaults(func=copy_all_used_php_files)

    return base_parser.parse_args(args)


def main(args):
    args_obj = parse_args(args)
    args_obj.func(args_obj)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
