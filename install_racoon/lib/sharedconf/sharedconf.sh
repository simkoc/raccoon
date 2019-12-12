#!/bin/bash

## Credit to Glenn Jackman http://stackoverflow.com/questions/23167047/bash-parse-arrays-from-config-file

while read line; do 
    if [[ $line =~ ^"["(.+)"]"$ ]]; then 
        arrname=${BASH_REMATCH[1]}
        declare -A $arrname
    elif [[ $line =~ ^([_[:alpha:]][_[:alnum:]]*)"="(.*) ]]; then 
        declare ${arrname}[${BASH_REMATCH[1]}]="${BASH_REMATCH[2]}"
    fi
done < $1

####
# Example of CFG file:
# 
# [section0]
# variable1=value1
#
# The loop above creates an associative array for each section:
# echo ${section0[variable1]}
####

