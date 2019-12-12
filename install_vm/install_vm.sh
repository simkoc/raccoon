#!/bin/bash

if [ $# -ne 6 ]; then
    echo "usage: ./install.sh </full/path/to/vm.ova> <vm-type> <vm-name> <user> <vm-ip> <pwd>"
    exit 1
fi

ova_path=$1
vmtype=$2
vmname=$3
user=$4
ip=$5
password=$6

# generate vdi path
path=`echo ${ova_path} | grep -Eo '.*[/]'`
vm_file_name=`basename $ova_path`
vm_file_name=`echo $vm_file_name | sed 's/\.ova//g'`
vdi_path="${path}${vm_file_name}-${vmname}.vdi"

# script internal constants
host_ip="NOT SET"
mount_point='/mnt'
hostonlyifs_count=`vboxmanage list hostonlyifs | grep GUID | wc -l`


if [ `vboxmanage list vms | grep $3 | wc -l` -gt 0 ]; then
    echo "ERROR: there exists already vm $3"
    echo "either choose another name or remove this vm"
    exit 1
fi


if [ "$hostonlyifs_count" == "1" ]; then
    host_ip=`vboxmanage list hostonlyifs | grep IPAddress | sed 's/IPAddress:[ ]*//'`
else
    echo "ERROR: there are currently $hostonlyifs_count hostonly vbox networks"
    echo "there must only be one. Resolve problem and restart script"
    exit 1
fi


./utils/ova_to_vdi.sh ${ova_path} ${vdi_path}

sudo ./utils/mount_vdi.sh --mount ${vdi_path} ${mount_point}

sudo ./utils/debian_setup_harddrive.sh ${mount_point} ${ip}

sudo ./utils/mount_vdi.sh --umount ${mount_point}

./utils/bitnami_add_vm.sh ${vdi_path} ${vmname}

echo "waiting for 120sec"
sleep 30
echo "waiting for 90sec"
sleep 30
echo "waiting for 60sec"
sleep 30
echo "waiting for 30sec"
sleep 30

bitnami_debian_evil_cronjob_file="./files/evil_cronjob"
echo "copying network_cronjob.sh"
sshpass -p ${password} scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ${bitnami_debian_evil_cronjob_file} bitnami@${ip}:network_cronjob.sh
echo "make network_cronjob.sh executable"
sshpass -p ${password} ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null bitnami@${ip} "chmod +x /home/bitnami/network_cronjob.sh"
echo "extracting crontab -l"
sshpass -p ${password} ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null bitnami@${ip} "crontab -l > cronjob_list"
echo "preping cronjob list"
sshpass -p ${password} ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null bitnami@${ip} "echo '* * * * * /home/bitnami/network_cronjob.sh' >> cronjob_list"
echo "inserting new cronjob list"
sshpass -p ${password} ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null bitnami@${ip} "crontab cronjob_list"
echo "cleanup the manipulated cronjob list"
sshpass -p ${password} ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null bitnami@${ip} "rm cronjob_list"


bitnami_credentials_file="${HOME}/tmp/.bitnami_credentials"
sshpass -p ${password} scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null bitnami@${ip}:bitnami_credentials ${bitnami_credentials_file}
vm_credentials=`grep -e "The default" ${bitnami_credentials_file}`
rm -f ${bitnami_credentials_file}

# move mysql proxy
echo "copying mysql-proxy on machine"
sshpass -p ${password} scp -r -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ./mysql-proxy-0.8.5-linux-glibc2.3-x86-64bit/ "${user}@${ip}":/home/bitnami/

# move lua script
echo "copying lua script on machine"
sshpass -p ${password} scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ./script.lua "${user}@${ip}":/home/bitnami/mysql-proxy-0.8.5-linux-glibc2.3-x86-64bit/

# move hashQuery.pex
sshpass -p ${password} scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ./hashQuery.pex "${user}@${ip}":/home/bitnami/

# start manipulating server vm
echo "configurating machine and starting proxy as well as restarting webapp"
sshpass -p ${password} ssh -tt -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "${user}@${ip}" '
sudo sed -i -e "s/3306/3307/g" "/opt/bitnami/mysql/my.cnf";
sudo sed -i -e "s/socket/#socket/g" "/opt/bitnami/mysql/my.cnf";
sudo sed -i -e "s/--port=3306//g" "/opt/bitnami/mysql/scripts/ctl.sh";
sudo sed -i -e "s/#LoadModule unique_id_module modules\/mod_unique_id.so/LoadModule unique_id_module modules\/mod_unique_id.so/g" "/opt/bitnami/apache2/conf/httpd.conf";
sudo sed -i -e "s/xdebug.trace_output_name=xdebug/xdebug.trace_output_name=xdebug.%R.%U/g" "/opt/bitnami/php/etc/php.ini";
sudo sed -i -e "s/pm.max_children=5/pm.max_children=20/g" "/opt/bitnami/php/etc/bitnami/common.conf";
sudo sed -i -e "s/pm.max_children=5/pm.max_children=20/g" "/opt/bitnami/php/etc/php-fpm.conf";
sudo sed -i -e "s/pm.max_children=5/pm.max_children=20/g" "/opt/bitnami/php/etc/common-dynamic.conf";
sudo sed -i "/LogFormat.* common/s/.*/&\nLogFormat \"\\\\\"%r\\\\\" \\\\\"%{UNIQUE_ID}e\\\\\"\" assoclog/" "/opt/bitnami/apache2/conf/httpd.conf";
sudo sed -i "/CustomLog \"logs\/access_log\" common/s/.*/&\nCustomLog \"logs\/assoc_log\" assoclog/" "/opt/bitnami/apache2/conf/httpd.conf";
sudo sed -i "/LogFormat.* common/s/.*/&\nLogFormat \"%t %r\" ground_data_log/" "/opt/bitnami/apache2/conf/httpd.conf";
sudo sed -i "/CustomLog \"logs\/access_log\" common/s/.*/&\nCustomLog \"logs\/ground_data_log\" ground_data_log/" "/opt/bitnami/apache2/conf/httpd.conf";
sudo sed -i "/LogFormat.* common/s/.*/&\nLogFormat %r oracle_log/" "/opt/bitnami/apache2/conf/httpd.conf";
sudo sed -i "/CustomLog \"logs\/access_log\" common/s/.*/&\nCustomLog \"logs\/oracle_log\" oracle_log/" "/opt/bitnami/apache2/conf/httpd.conf";
sudo echo "Timeout 600" >> "/opt/bitnami/apache2/conf/httpd.conf";
sudo echo "ProxyTimeout 600" >> "/opt/bitnami/apache2/conf/httpd.conf"'

# change webapp config
case "${vmtype}" in
     abantecart) 
        echo "changing config of abantecart"
        sshpass -p ${password} ssh -tt -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "${user}@${ip}" '
sudo sed -i -e "s/localhost/127.0.0.1/g" "/opt/bitnami/apps/abantecart/htdocs/system/config.php"'

        ;;
     mybb)
        echo "changing config for mybb"
        sshpass -p ${password} ssh -tt -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "${user}@${ip}" '
sudo sed -i -e "s/localhost:3306/127.0.0.1:3306/g" "/opt/bitnami/apps/mybb/htdocs/inc/config.php";
sudo sed -i -e "s/httpd.conf/httpd-large.conf/g" "/opt/bitnami/apache2/conf/httpd.conf";
sudo sed -i -e "s/ondemand/static/g" "/opt/bitnami/php/etc/php-fpm.conf"'

        ;;
    opencart)
        echo "changing config for opencart"
        sshpass -p ${password} ssh -tt -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "${user}@${ip}" '
sudo sed -i -e "s/localhost/127.0.0.1/g" "/opt/bitnami/apps/opencart/htdocs/config.php";
sudo sed -i -e "s/localhost/127.0.0.1/g" "/opt/bitnami/apps/opencart/htdocs/admin/config.php"'

	;;
    oxid)
	echo "changing config for oxid"
	sshpass -p ${password} ssh -tt -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "${user}@${ip}" '
sudo sed -i -e "s/localhost/127.0.0.1/g" "/opt/bitnami/apps/oxid/htdocs/source/config.inc.php";
sudo sed -i -e "s/httpd.conf/httpd-large.conf/g" "/opt/bitnami/apache2/conf/httpd.conf";
sudo sed -i -e "s/ondemand/static/g" "/opt/bitnami/php/etc/php-fpm.conf"'

        ;;
    simplemachinesforum)
	echo "changing config for simplemachinesforum"
	sshpass -p ${password} ssh -tt -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "${user}@${ip}" '
sudo sed -i -e "s/localhost/127.0.0.1/g" "/opt/bitnami/apps/simplemachinesforum/htdocs/Settings.php";
sudo sed -i -e "s/httpd.conf/httpd-large.conf/g" "/opt/bitnami/apache2/conf/httpd.conf";
sudo sed -i -e "s/ondemand/static/g" "/opt/bitnami/php/etc/php-fpm.conf"'
esac

echo "restarting and starting proxy"
sshpass -p ${password} ssh -tt -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "${user}@${ip}" '
sudo /opt/bitnami/ctlscript.sh restart >> /dev/null;
sudo touch /home/bitnami/suspendSingleQuery.txt;
sudo echo "yeah I bloody reached this point";
screen -d -S mysqlproxy -m /home/bitnami/mysql-proxy-0.8.5-linux-glibc2.3-x86-64bit/bin/mysql-proxy --proxy-address 127.0.0.1:3306 --proxy-backend-addresses 127.0.0.1:3307 --proxy-lua-script /home/bitnami/mysql-proxy-0.8.5-linux-glibc2.3-x86-64bit/script.lua --log-file /home/bitnami/mysql-proxy-0.8.5-linux-glibc2.3-x86-64bit/error.log;
echo `screen -ls`;
sleep 5;'


echo "creating new snapshot racoon-ready"
vboxmanage snapshot $vmname take "racoon-ready"
echo "powering the sucker down"
vboxmanage controlvm $vmname poweroff

echo "vm ${vmname} successfully installed"
