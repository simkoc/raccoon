# How To Racoon

Racoon is designed to apply the approach proposed by Paleari et al. on data gathered by Deemon, a tool
build by Pellegrino et al., to detect and verify Web Application Race Conditions (WARCs) within the same request.

This tutorial will cover all the steps necessary to perform such an analysis from start to end for a single use case on a single web application.

We first cover the software that is required and then proceed to the application usage in the order it is needed:

1. ground truth gathering using racoon data-gathering script
1. using the data gathered from step 1 to extract possible WARC candidates/verifying those

## Software Needed

* postgresql 
* python 2.7
* python 3.5 (yeah I know python is a mess)
* virtualenv
* pip
* neo4j
* Firefox (with Selenium IDE)
* VirtualBox

## Installation

Besides installing the before mentioned software just execute the steps as described as below and if some software/dependency is missing install said dependency and note it down (here). I strongly suggest working in a virtual environment for everything python related to prevent cluttering of the global workspace.

### Special Libraries

* Modified version of sqlparse (https://github.com/simkoc/sqlparse)
* Modified version of py2neo (https://github.com/tgianko/py2neo.git#egg=py2neo)

## Pre-Prep

Install the database schema using the script located in `./detector/database`

## Ground Truth Gathering using Deemon

### Preparation:

The first step is to 'install' the virtual machine the usecase is supposed to be run against. Those machines can be acquired from bitnami.com and we assume from here on that the VM used is a bitnami provided one even though the overall approach is not specific to bitnami provided machines. To install the corresponding machine use `install_vm.sh` in the `./install_vm/` folder - the IP may be chosen abitrarily within 192.168.56.0/24. 
	   
Wait until the script finishes (may take a while) and ensure that virtualbox now has a virtual machine registered with the state `virgin-state-mysql-proxy`.

First the wanted use case recipe has to be selected or generated. The generation can be done by opening the Selenium IDE and recording all the steps belonging to the use case. Then saving the steps. We will refer to this use case recipe as `recipe.html` from here on.

Note: Everytime you are gathering data and you need certain properties for making your recipe work you have to save them as the virgin state in your VM.
E.g. running a recipe for user-login, you have to create the user in your web-shop so selenese is actually able to login a valid user.

### Gathering Data

To gather data based on the virtual machine and the recipe the `./data_gathering.sh` in `./data_gathering` is used.

       ./data_gatherin.sh <proj_name> <operation> <user_in_testcase> <vm_name> <vm_user> <vm_password> <vm_state> <vm_ip> <full_path_to_selenese_jar> <total_timeout_for_selenese_in_ms> <selenese_speed> <full_path_to_firefox> <full_path_to_screenshot_folder> <full_path_to_selenese_recipe>
	  
Now we are done with gathering of the basic data.

## Detecting and Verifying WARCs using Racoon

### Preparation:

First firebases have to be started over which the different requests are routed. This is done via `./start-firebase-same-ip.sh` in `/racoon/testor/distributedSelenese`:

      ./start-firebase-same-ip.sh
      
A list of the firebases has to be created for making racoon run properly. So put the firebases listed after running `./start-firebase-same-ip.sh´ into a variable called `firebases` listing as csv their IPs:

      firebases=firebase-0,firebase-1...
	  
### Running Tests:

This command runs a full test for the given use case on the given virtual machine. In the end the database has to be checked for race condition candidates where the racoon baseline gathering (automatically done at the start) has a lower success rate than the actual test.

      ./racoon.py full localhost trueschottsman woulddothat <sql-db-name> <db-host> <neo4j-user> <neo4j-pwd> -1 <experiment-id> bitnami <vm-ip> bitnami /tmp/ <vm-name> <vm-state-name> /path/to/recipe/folder/ ${firebases} 3 --relaxed-check
