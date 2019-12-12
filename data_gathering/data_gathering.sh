#!/bin/bash

# this script is gathering the ground data needed for racoon. It is using selenese to run szenarios on the installed virtual machine.
# as selenese often crashes the script takes screenshot of the situation where it does so.

if [ $# -ne 17 ]; then
    echo "usage: ./data_gathering.sh <db_host> <db_user>  <db_pwd> <db_name> <proj_name> <operation> <user_in_testcase> <vm_name> <vm_user> <vm_password> <vm_state> <vm_ip> <full_path_to_selenese_jar> <total_timeout_for_selenese_in_ms> <selenese_speed> <full_path_to_firefox> <full_path_to_selenese_recipe>"
    exit 1
fi

db_host=$1
db_user=$2
db_pwd=$3
db_name=$4
proj_name=$5
operation=$6
tc_user=$7
vm_name=$8
vm_user=$9
vm_pw=${10}
vm_state=${11}
vm_ip=${12}
selenese_path=${13}
sel_timeout=${14}
sel_speed=${15}
firefox_path=${16}
testcase_path=${17}

vm_url="http://$vm_ip"
vm_url_ssl="https://$vm_ip"

echo "restoring snapshot $vm_state"
echo $vm_url
vboxmanage snapshot ${vm_name} restore ${vm_state}

echo "starting up machine $vm_name"
vboxmanage startvm ${vm_name} --type headless

echo "waiting for vm connecting to network"
#echo "120sec"
#sleep 30
echo "90sec"
sleep 30
echo "60sec"
sleep 30
echo "30sec"
sleep 30

logs="${HOME}/.racoon/data/data_gathering/logs/"
xdebugs="${HOME}/.racoon/data/data_gathering/xdebugs/"
xdebug_list="${HOME}/.racoon/data/data_gathering/xdebugs.list"
screenshot_folder="${HOME}/.racoon/data/screenshots/"
headless="--headless"
#headless=""

#wipe data of former runs
echo "wiping data of former runs on local machine"
rm "${logs}"*log*
rm "${xdebugs}"*
rm "${xdebug_list}"

echo "wiping data of former runs on virtual machine"
sshpass -p ${vm_pw} ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ${vm_user}@${vm_ip} "sudo bash -c 'echo > /opt/bitnami/apache2/logs/ground_data_log'"
sshpass -p ${vm_pw} ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ${vm_user}@${vm_ip} "sudo bash -c 'echo > /opt/bitnami/apache2/logs/oracle_log'"

echo "starting sel-runner"

java -jar ${selenese_path} --driver firefox --firefox ${firefox_path} --no-proxy *.com,*.net,*.org -t ${sel_timeout} --set-speed ${sel_speed} -b ${vm_url} --height 1080 --width 1920 ${headless} --screenshot-on-fail ${screenshot_folder} ${testcase_path}
status1=$?

echo "waiting 30sec"
sleep 30

#copy first apache-log-file to local machine
echo "moving log-file to local machine"
sshpass -p ${vm_pw} scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ${vm_user}@${vm_ip}:/opt/bitnami/apache2/logs/oracle_log $logs/apache_log_1

#copy log for httprequests to local machine
echo "moving log-file to local machine"
sshpass -p ${vm_pw} scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ${vm_user}@${vm_ip}:/opt/bitnami/apache2/logs/ground_data_log $logs/ground_data_log

#copy xdebugs to local machine
echo "moving xdebugs to local machine"
sshpass -p ${vm_pw} scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ${vm_user}@${vm_ip}:/tmp/*.xt $xdebugs
echo "removing unrelevant xdebugs"

for file in $xdebugs/*.xt; do
    length=${#file}
    char=${file:$length - 10}

    if [[ $char == .* ]]; then
        rm $file
    fi
done

#set remaining xdebugs to a list
ls $xdebugs/*.xt > ${xdebug_list}

echo "ready for second run"

echo "shutting down vm"
vboxmanage controlvm ${vm_name} poweroff

echo "restoring snapshot $vm_state"
vboxmanage snapshot ${vm_name} restore ${vm_state}

sleep 20

echo "starting up machine $vm_name"
vboxmanage startvm ${vm_name} --type headless

echo "waiting for vm connecting to network"
#echo "120sec"
#sleep 30
echo "90sec"
sleep 30
echo "60sec"
sleep 30
echo "30sec"
sleep 30

echo "wiping data of former runs on virtual machine"
sshpass -p ${vm_pw} ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ${vm_user}@${vm_ip} "sudo bash -c 'echo > /opt/bitnami/apache2/logs/ground_data_log'"
sshpass -p ${vm_pw} ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ${vm_user}@${vm_ip} "sudo bash -c 'echo > /opt/bitnami/apache2/logs/oracle_log'"

echo "starting sel-runner"
java -jar ${selenese_path} --driver firefox --firefox ${firefox_path} --no-proxy *.com,*.net,*.org -t ${sel_timeout} --set-speed ${sel_speed} -b ${vm_url} --height 1080 --width 1920 ${headless} --screenshot-on-fail ${screenshot_folder} ${testcase_path}
status2=$?

echo "waiting 30sec"
sleep 30

#copy second apache-log-file to local machine
echo "moving log-file to local machine"
sshpass -p ${vm_pw} scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ${vm_user}@${vm_ip}:/opt/bitnami/apache2/logs/oracle_log $logs/apache_log_2

vboxmanage controlvm ${vm_name} poweroff

#check status codes of sel-runner
if [ $status1 -eq 0 ] && [ $status2 -eq 0 ]; then
    status="true"
else
    status="false"
fi

#creating database entry
echo "creating database entry"
echo "python ../database.py ${db_host} ${db_user} ${db_pwd} ${db_name} ${proj_name} S1/2 ${operation} ${tc_user} ${sel_speed} now ${status} ${testcase_path} ${vm_url_ssl}"
python ../database.py $db_host $db_user $db_pwd $db_name $proj_name S1/2 $operation $tc_user $sel_speed now $status $testcase_path $vm_url_ssl

if [ "$status" = "true" ]; then
    exit 0
else
    exit 1
fi