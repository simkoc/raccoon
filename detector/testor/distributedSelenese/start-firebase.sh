#!/bin/bash

#./createVirtualNetworks.sh epn0s3 9

for counter in `seq 0 9`;
do
    echo "starting firebase tmux session 'firebase-$counter'"
    echo tmux new -d -s "firebase-${counter}" "xvfb-run -a ip netns exec ns${counter} python firebase.py 404${counter}"
    echo `tmux new -d -s "firebase-${counter}" "xvfb-run -a ip netns exec ns${counter} python firebase.py 404${counter}"`
done
  
