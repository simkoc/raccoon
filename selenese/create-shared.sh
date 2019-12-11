#!/bin/bash

# DB_PATH="/home/seasurf/.vilanoo/"
PROJ_PATH="/home/seasurf/deemon/"
SELEN_PATH="/home/seasurf/usenix/selenese-testcases/"
CONF_PATH="${SELEN_PATH}/config/"
FIREFOX_BIN="/home/seasurf/firefox/firefox"

function run-test {
    data=(${1//-/ })
    projname=${data[0]}
    user=${data[3]}
    operation=${data[4]}
    cd $PROJ_PATH
    if [ "$projname" = "pc" ]
    then
       projname="prestashop"
       #echo Overriding
    else if [ "$projname" = "in" ]
         then
            projname="invoiceninja"
         else if [ "$projname" = "si" ]
              then
                 projname="simpleinvoice" 
	      else if [ "$projname" = "smf" ]
                   then
                      projname="simplemachinesforum"
                   else if [ "$projname" = "myBB" ]
                        then
                           projname="mybb"

                        fi
                   fi
              fi
         fi
	     
    fi
    config="${projname}.cfg"
    echo ./run-test.sh ${CONF_PATH}/local.cfg ${CONF_PATH}/${config} ${2} ${operation} ${user} vilanoo-${projname} ${4}  ${3} ${SELEN_PATH}/${projname}/${1}.html
    ./run-test.sh ${CONF_PATH}/local.cfg ${CONF_PATH}/${config} ${2} ${operation} ${user} vilanoo-${projname} ${4}  ${3} ${SELEN_PATH}/${projname}/${1}.html
    
    # echo ./run-test.sh vilanoo-${projname} 192.168.56.101 ${4} ${projname}-${user}-${operation}_${2} ${3} ${SELEN_PATH}/${projname}/${1}.html ${FIREFOX_BIN} 3333 3334
    # ./run-test.sh vilanoo-${projname} 192.168.56.101 ${4} ${projname}-${user}-${operation}_${2} ${3} ${SELEN_PATH}/${projname}/${1}.html ${FIREFOX_BIN} 3333 3334
}

function rawtrace-analysis {
    cd ${PROJ_PATH}rawtrace-analysis/src/
    echo ">>>>>" ./run-analyzer.sh -v ${1} -m ${2} -d ${3} -S ${PROJ_PATH}data/DBSchema.sql
                 ./run-analyzer.sh -v ${1} -m ${2} -d ${3} -S ${PROJ_PATH}data/DBSchema.sql &> ${4}-analyzer.log
}

function dbmanager {
    cd ${HOME}/
    source virtenv/vilanoo/venv/bin/activate
    cd ${PROJ_PATH}deep-modeling/
    echo ">>>>>" ./dbmanager.py ${1} ${2} ${3} ${4} ${5} ${6}
    echo ${7}-dbmanager-import.log
    #./dbmanager.py import all ${1} ${2} ${3} ${4} ${5} ${6} &> ${7}-dbmanager-import.log
    #./dbmanager.py analysis all ${4} ${5} ${6} &> ${7}-dbmanager-analysis.log
    ./dbmanager.py analysis abssql ${4} ${5} ${6} &> ${7}-dbmanager-abssql.log
    deactivate
}
