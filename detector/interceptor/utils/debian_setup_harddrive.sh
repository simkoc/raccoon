#!/bin/bash

set -e

if [ $# -ne 2 ]; then
    echo "usage: ./debian_setup_harddrive.sh <mount-point> <vm-ip>"
    exit 1
fi


# Parameter
mount_point=$1
ip_address=$2

# Constants
bitnami_debian_network_setup_file="./files/debian_network"
bitnami_debian_etc_shadow_file="./files/debian_shadow"
bitnami_debian_sshd_service_file="./files/sshd.service"
bitnami_debian_evil_cronjob_file="./files/evil_cronjob"
apache_config="${mount_point}/opt/bitnami/apache2/conf/httpd.conf"

# then configure the setup for the network
sed "s/IPADDRESS/${ip_address}/g" ${bitnami_debian_network_setup_file} > ${mount_point}/etc/network/interfaces.d/setup
# echo "* * * * /home/bitnami/evil_cronjob.sh" >> ${mount_point}/var/spool/cron/crontabs/bitnami
# cat ${bitnami_debian_evil_cronjob_file} > ${mount_point}/home/bitnami/evil_cronjob.sh
# chown bitnami:bitnami ${mount_point}/home/bitnami/evil_cronjob.sh
# chmod +x ${mount_point}/home/bitnami/evil_cronjob.sh


# enabling generic passwords
cp ${bitnami_debian_etc_shadow_file} "${mount_point}/etc/shadow"
chmod "u-x,g-x,o-wx" "${mount_point}/etc/shadow"


#enabling ssh
rm -f ${mount_point}/etc/ssh/sshd_not_to_be_run
ln -s ${mount_point}/lib/systemd/system/sshd.system ${mount_point}/etc/systemd/system/ssh.service
# cp ${bitnami_debian_sshd_service_file} ${mount_point}/etc/systemd/system/sshd.service
# cp ${bitnami_debian_sshd_service_file} ${mount_point}/lib/systemd/system/ssh.service
# chmod 777 ${mount_point}/etc/systemd/system/sshd.service
# chmod 644 ${mount_point}/lib/systemd/system/ssh.service

#- enabling root login with root account
sed -i -- 's/#PermitRootLogin prohibit-password/PermitRootLogin Yes/g' "${mount_point}/etc/ssh/sshd_config" 

# enabling uid to request matching
sed -i -e "s/#LoadModule unique_id_module modules\/mod_unique_id.so/LoadModule unique_id_module modules\/mod_unique_id.so/g" "${mount_point}/opt/bitnami/apache2/conf/httpd.conf";
sed -i "/LogFormat.* common/s/.*/&\nLogFormat \"\\\\\"%r\\\\\" \\\\\"%{UNIQUE_ID}e\\\\\"\" unique/" "${mount_point}/opt/bitnami/apache2/conf/httpd.conf";
sed -i "/CustomLog \"logs\/access_log\" common/s/.*/&\nCustomLog \"logs\/unique_log\" unique/" "${mount_point}/opt/bitnami/apache2/conf/httpd.conf";

echo ""                                                                 >> "${mount_point}/opt/bitnami/php/etc/php.ini"
echo "[XDebug]"                                                         >> "${mount_point}/opt/bitnami/php/etc/php.ini"
echo "zend_extension=\"/opt/bitnami/php/lib/php/extensions/xdebug.so\"" >> "${mount_point}/opt/bitnami/php/etc/php.ini"
echo "xdebug.auto_trace=1"                                              >> "${mount_point}/opt/bitnami/php/etc/php.ini"
echo "xdebug.collect_params=4"                                          >> "${mount_point}/opt/bitnami/php/etc/php.ini"
echo "xdebug.trace_format=1"                                            >> "${mount_point}/opt/bitnami/php/etc/php.ini"
echo "xdebug.collect_return=1"                                          >> "${mount_point}/opt/bitnami/php/etc/php.ini"
echo "xdebug.collect_assignments=1"                                     >> "${mount_point}/opt/bitnami/php/etc/php.ini"
echo "xdebug.trace_options=0"                                           >> "${mount_point}/opt/bitnami/php/etc/php.ini"
echo "xdebug.trace_output_dir=/tmp/"                                    >> "${mount_point}/opt/bitnami/php/etc/php.ini"
echo "xdebug.trace_output_name=xdebug.%R.%U"                            >> "${mount_point}/opt/bitnami/php/etc/php.ini"
echo "xdebug.var_display_max_data=16000"                                >> "${mount_point}/opt/bitnami/php/etc/php.ini"

#disabling apache mod_pagespeed
sed -i 's/Include conf\/pagespeed.conf/#Include conf\/pagespeed.conf/g' $apache_config
sed -i 's/Include conf\/pagespeed_libraries.conf/#Include conf\/pagespeed_libraries.conf/g' $apache_config
