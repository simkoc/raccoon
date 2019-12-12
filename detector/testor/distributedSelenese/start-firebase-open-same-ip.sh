#!/bin/bash

LOG_FOLDER="${HOME}/.racoon/firebases/"

for counter in `seq 0 9`;
do
	echo "starting firebase tmux session 'firebase-${counter}'"
	echo tmux new -d -s "firebase-${counter}" "ip netns exec ns3${counter} python firebase.py 404${counter}"
	gnome-terminal -x /bin/bash -c "python firebase.py 404${counter} > >(tee -a ${LOG_FOLDER}/404${counter}.log) 2> >(tee -a ${LOG_FOLDER}/404${counter}.log)"
done
