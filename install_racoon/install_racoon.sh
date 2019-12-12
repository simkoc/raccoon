# This script is installing racoon on your machine
# Installation prerequisites:
#	- Python mess including
#		- Python 2.7
#		- Python 3.7
#	    	- Pip
#	- Virtualenv
#	- Latest Firefox
#	- Java
#   	- xvfb
#	- Virtualbox
#	- Postgresql
#       - create user for database (as an example we used "trueschottsman". If you choose a different username you have to adjust "permissions.sql" located at /detector/database)
#       - create database schema with "installDatabase.sh" located at /detector/database


# Creating hostonly interface
vboxnumber=$(vboxmanage hostonlyif create | tr -dc '0-9')
vboxmanage hostonlyif ipconfig vboxnet$vboxnumber --ip 192.168.56.1

# Creating folder structure in home folder
mkdir ~/.racoon
cp requirements.txt ~/.racoon
cp -r lib ~/.racoon
cd ~/.racoon
mkdir data
mkdir data/data_gathering
mkdir data/screenshots
mkdir data/data_gathering/logs
mkdir data/data_gathering/xdebugs
mkdir Virtualenv
mv requirements.txt Virtualenv
mv lib Virtualenv/
mkdir firebases

# Creating virtual environment and installing packages
cd ~/.racoon/Virtualenv
virtualenv racoon
cd racoon
source bin/activate
pip install -r ~/.racoon/Virtualenv/requirements.txt
pip install  ~/.racoon/Virtualenv/lib/mosgi
pip install  ~/.racoon/Virtualenv/lib/selrun
pip install  ~/.racoon/Virtualenv/lib/sharedconf
pip install  ~/.racoon/Virtualenv/lib/xdebugparser

#Downloading selenese-runner and geckodriver
cd ~/.racoon/firebases
wget -O "selenese-runner.jar" https://github.com/vmi/selenese-runner-java/releases/download/selenese-runner-java-3.26.0/selenese-runner.jar
wget -O "geckodriver.tar.gz" https://github.com/mozilla/geckodriver/releases/download/v0.25.0/geckodriver-v0.25.0-linux64.tar.gz
tar xvzf geckodriver.tar.gz
rm geckodriver.tar.gz
