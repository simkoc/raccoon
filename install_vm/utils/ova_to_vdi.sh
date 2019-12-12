#!/bin/bash

if [ $# -ne 2 ]; then
    echo "usage: ./ova_to_vdi.sh </full/path/to/vm.ova> </full/path/to/target/vm.vdi>"
    exit 1
fi


buffer_folder="${HOME}/tmp/.ovabuff/"
ova_path=$1
vdi_file_path=$2


mkdir ${buffer_folder}

tar -xf ${ova_path} -C ${buffer_folder}
vmdk_file="${buffer_folder}`ls ${buffer_folder} | grep vmdk`"
vboxmanage clonehd ${vmdk_file} ${vdi_file_path} --format vdi 
chmod 666 ${vdi_file_path}
vboxmanage closemedium disk ${vmdk_file} --delete

rm -r ${buffer_folder}

