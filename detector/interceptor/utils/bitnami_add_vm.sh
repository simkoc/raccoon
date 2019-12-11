#!/bin/bash

if [ $# -ne 2 ]; then
    echo "usage: ./bitnami_add_vm.sh </full/path/to/vm.vdi> <vm-name>"
    exit 1
fi

# PARAMETER
vdi_path=$1
vm_name=$2


#CONSTANTS
hostonly_adapter_name=`vboxmanage list hostonlyifs | grep "Name" | head -n1 | sed 's/Name:[ ]*//'`

echo "install hostonly adapter ${hostonly_adapter_name}"

rm -rf $HOME/.vilanoo/${vm_name}/


vboxmanage createvm --name ${vm_name} --basefolder $HOME/.vilanoo/
vboxmanage registervm $HOME/.vilanoo/${vm_name}/${vm_name}.vbox
vboxmanage storagectl ${vm_name} --add sata --name "SCSI Controller"
vboxmanage storageattach ${vm_name} --storagectl "SCSI Controller" --medium ${vdi_path} --port 0 --type hdd

vboxmanage modifyvm ${vm_name} --memory 1024 
vboxmanage modifyvm ${vm_name} --cpus 2       
vboxmanage modifyvm ${vm_name} --ioapic on    
vboxmanage modifyvm ${vm_name} --nic1 hostonly --nictype1 82540EM --hostonlyadapter1 ${hostonly_adapter_name}


vboxmanage startvm ${vm_name}
