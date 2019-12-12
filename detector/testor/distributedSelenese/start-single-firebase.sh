#!/bin/bash

if [ $# -ne 3 ]; then
    echo "usage: ./start-firebase-same-ip.sh <firebase-port> <max_fuse_delay> <walzing_barrage_timer>"
    exit 1
fi

firebase_port=$1
max_fuse_delay=$2
walzing_barrage_timer=$3
counter=${firebase_port: -1}
current_path="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
firebase_script_path="${current_path%.*}/firebase.py"
LOG_FOLDER="${HOME}/.racoon/firebases/"

echo "starting firebase tmux session 'firebase-${counter}'"
tmux new -d -s "firebase-${counter}" "xvfb-run -a python $firebase_script_path 404${counter} $max_fuse_delay $walzing_barrage_timer > >(tee -a ${LOG_FOLDER}/404${counter}.log) 2> >(tee -a ${LOG_FOLDER}/404${counter}.log)"
# tmux new -d -s firebase-0 xvfb-run -a python /home/tim/git/hiwi/racoon/detector/testor/distributedSelenese/firebase.py 4040 1200000 30000> >(tee -a /home/tim/.racoon/firebases/4040.log) 2> >(tee -a /home/tim/.racoon/firebases/4040.log)
