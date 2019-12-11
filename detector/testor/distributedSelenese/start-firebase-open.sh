#!/bin/bash

LOG_FOLDER="/home/seasurf/firebases/"

for counter in `seq 0 9`;
do
	echo "starting firebase tmux session 'firebase-${counter}'"
	echo tmux new -d -s "firebase-${counter}" "ip netns exec ns3${counter} python firebase.py 404${counter}"
	sudo gnome-terminal -x /bin/bash -c "ip netns exec ns3${counter} python firebase.py 404${counter} > >(tee ${LOG_FOLDER}/404${counter}.log) 2> >(tee ${LOG_FOLDER}/404{counter}.log)"
done
