#!/bin/bash

for counter in `seq 0 9`;
do
        echo "killing firebase tmux session 'firebase-${counter}'"
        tmux kill-session -t "firebase-${counter}"
done
