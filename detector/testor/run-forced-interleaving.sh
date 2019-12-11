#!/bin/bash

if [ $# -ne 10 ]; then
    echo "usage: ./run-forced-interleaving.sh <vm-name> <vm-state> <user> <vm-ip> <password> <selenese-ts> <query> <firebases> <refX> <parallel-count>"
    exit 1
fi


vmname=$1
vmstate=$2
user=$3
vmip=$4
password=$5
ts=$6
query=$7
firebases=$8
refX=$9
amount=${10}
xpath="/tmp/"
base_url="http://${vmip}"
selenese=/home/simkoc/hiwi/csrf/vilanoo/selenese-runner/selenese-runner.jar
firefox=/home/simkoc/hiwi/csrf/firefox/firefox

if vboxmanage list vms | grep --quiet "\"${vmname}\""; then
    
    if vboxmanage list runningvms | grep --quiet "\"${vmname}\""; then
        echo "I am sorry, Dave. I am afraid I cannot do that"
	echo "test vm ${vmname} is currently running - shut down before trying again"
	exit 1
    else
	echo `vboxmanage snapshot ${vmname} restore ${vmstate}`
	echo `vboxmanage startvm ${vmname} --type headless`
    fi
    
else
    echo "machine ${vmname} is unknown"
    exit 1
fi


echo "waiting for you to log into the vm and connect to screen"
sleep 5
echo "you may now log in"
sleep 10


# configuration of the interceptor infrastructure
echo ./../interceptor/setQuery.sh ${user} ${vmip} ${password} "${query}"
./../interceptor/setQuery.sh ${user} ${vmip} ${password} "${query}"


# running the forced interleaving test on the configured interceptor
echo python run-forced-interleaving-test.py ${ts} ${vmip} ${user} ${password} ${xpath} ${firebases} ${refX} ${amount}
python run-forced-interleaving-test.py simpleInterleaving ${ts} ${vmip} ${user} ${password} ${xpath} ${firebases} ${refX} ${amount}


echo `vboxmanage controlvm ${vmname} poweroff`
