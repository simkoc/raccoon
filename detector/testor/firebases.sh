#!/bin/bash

firebases=(\
"firebase-alpha" \
"firebase-beta"  \
"firebase-gamma" \
"firebase-delta" \
"firebase-epsilon" \
"firebase-zeta" \
"firebase-eta" \
"firebase-theta" \
"firebase-iota" \
"firebase-kappa")


function start_up {
    for firebase in "${firebases[@]}"
    do
        echo "getting ready state ${firebase}"
        echo `vboxmanage snapshot ${firebase} restore ready`
        echo "starting ${firebase}"
        echo `vboxmanage startvm ${firebase} --type headless`
    done
}



function shut_down {
    for firebase in "${firebases[@]}"
    do
        echo "stopping ${firebase}"
        echo `vboxmanage controlvm ${firebase} poweroff`
    done
}   



case $1 in
    "--start")
        start_up;;

    "--stop")
        shut_down;;
esac
