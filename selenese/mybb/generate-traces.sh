#!/bin/bash

PROJ_PATH="/home/seasurf/deemon/"
SELEN_PATH="/home/seasurf/usenix/selenese-testcases/"
CONF_PATH="${SELEN_PATH}/config/"
FIREFOX_BIN="/home/seasurf/firefox/firefox"
VM_NAME="vilanoo-mybb"
VM_IP="192.168.56.104"
PAT=`pwd`

echo ${PAT}

declare -a ts=(\
        "merged_TS_login-create-new-thread_admin1"\
        # "merged_TS_send-private-message_admin1"\
	"merged_TS_use-search-function_admin1"\
	"merged_TS_login-fail_admin1"\
)


for t in "${ts[@]}"
do
    data=(${t//_/ })
    echo "getting data on ${data[2]}"
    pushd ${PROJ_PATH}
    echo ${PAT}
    echo ./run-test.sh ${CONF_PATH}/local.cfg ${CONF_PATH}/mybb.cfg "S1" ${data[2]} ${data[3]} ${VM_NAME} ${VM_IP} "virgin-state" "${PAT}/${t}.html"
    xvfb-run ./run-test.sh ${CONF_PATH}/local.cfg ${CONF_PATH}/mybb.cfg "S1" ${data[2]} ${data[3]} ${VM_NAME} ${VM_IP} "virgin-state" "${PAT}/${t}.html"
    popd
done
