#!/bin/bash
#This file exists to run racoon over an entire folder of config files. Give your folder containing config files as argument. (example config files are given in ./example_conf

if [ $# -ne 1 ]; then
    echo "usage: ./automatic_run.sh <folder>"
    exit 1
fi

folder=$1

for filename in $folder/*.conf; do
	./racoon.py config $filename
done

