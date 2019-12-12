#!/bin/bash

ROUTER=0.0.0.0

function create_vlan {
    echo "ip netns add ns$1"
    ip netns add "ns$1"
    echo "ip link add link ${networkinterface} "ipvl$1" type ipvlan mode l2"
    ip link add link ${networkinterface} "ipvl$1" type ipvlan mode l2
	# echo 3
    ip link set dev "ipvl$1" netns "ns$1"
	# echo 4
    ip netns exec "ns$1" ip link set dev "ipvl$1" up
	# echo 5
    ip netns exec "ns$1" ip link set dev lo up
	# echo 6
    ip netns exec "ns$1" ip -4 addr add 127.0.0.1 dev lo
	# echo 7
    ip netns exec "ns$1" ip -4 addr add $2 dev "ipvl$1"
	# echo 8
    ip netns exec "ns$1" ip -4 route add default via ${ROUTER} dev "ipvl$1"
    #ip netns exec ns$1 ip -4 route add default gw 192.168.56.1 dev "ipvl$1"
}


networkinterface=$1

declare -i metab amount
amount=$2
amount+=30

echo $amount

for i in `seq 30 ${amount}`;
do
    declare -i metab counter
    counter=`expr $i - 30`
    ip="192.168.56.1$i"
    echo "creating vlan ns${i} with ip $ip"
    create_vlan ${i} ${ip}
    echo "created vlan ns${i} with ip $ip"
done
