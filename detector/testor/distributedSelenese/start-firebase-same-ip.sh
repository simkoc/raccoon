#!/bin/bash

if [ $# -ne 1 ]; then
    echo "usage: ./start-firebase-same-ip.sh </full/path/to/racoon/repository>"
    exit 1
fi
racoon_path=$1
firebase_script_path="$racoon_path/detector/testor/distributedSelenese/firebase.py"
LOG_FOLDER="${HOME}/.racoon/firebases/"

for counter in `seq 0 9`;
do
	echo "starting firebase tmux session 'firebase-${counter}'"
	echo tmux new -d -s "firebase-${counter}" "ip netns exec ns3${counter} python $firebase_script_path 404${counter}"
	tmux new -d -s "firebase-${counter}" "xvfb-run -a python $firebase_script_path 404${counter} > >(tee -a ${LOG_FOLDER}/404${counter}.log) 2> >(tee -a ${LOG_FOLDER}/404${counter}.log)"
done
