#!/bin/bash

user=$1
ip=$2
password=$3
query_string=$4

# create new file with query
echo echo "$4" > temp.txt
echo "$4" > temp.txt

# move new file with query
sshpass -p ${password} scp ./temp.txt "${user}@${ip}":/opt/suspendSingleQuery.txt

echo "done! Have fun honey :*"
