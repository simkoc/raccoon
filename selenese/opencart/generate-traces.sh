#!/bin/bash

PROJ_PATH="/home/seasurf/deemon/"
SELEN_PATH="/home/seasurf/usenix/selenese-testcases/"
CONF_PATH="${SELEN_PATH}/config/"
FIREFOX_BIN="/home/seasurf/firefox/firefox"
VM_NAME="vilanoo-opencart"
VM_IP="192.168.56.102"
PAT=`pwd`
WEBAPP="opencart"

echo ${PAT}

declare -a ts=(\
        "merged_TS_buy-canon-using-coupon_user"\
        "merged_TS_buy-canon-using-voucher_user"\
	"merged_TS_buy-other-canon-using-points_user"\
	"merged_TS_login-fail_user"\
)


for t in "${ts[@]}"
do
    data=(${t//_/ })
    echo "getting data on ${data[2]}"
    pushd ${PROJ_PATH}
    echo ${PAT}
    echo ./run-test.sh ${CONF_PATH}/local.cfg ${CONF_PATH}/${WEBAPP}.cfg "S1" ${data[2]} ${data[3]} ${VM_NAME} ${VM_IP} "config-done" "${PAT}/${t}.html"
    xvfb-run ./run-test.sh ${CONF_PATH}/local.cfg ${CONF_PATH}/${WEBAPP}.cfg "S1" ${data[2]} ${data[3]} ${VM_NAME} ${VM_IP} "config-done" "${PAT}/${t}.html"
    popd
done
