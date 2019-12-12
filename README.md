# How To Racoon

Racoon is designed to apply the approach proposed by Paleari et al. on data gathered by Deemon, a tool
build by Pellegrino et al., to detect and verify Web Application Race Conditions (WARCs) within the same request.

This tutorial will cover all the steps necessary to perform such an analysis from start to end for a single use case on a single web application.

We first cover the software that is required and then proceed to the application usage.

## Software Needed

* postgresql 
* python 2.7
* python 3.5 (yeah I know python is a mess)
* virtualenv
* pip
* Firefox (with Selenium IDE)
* VirtualBox
* Java 
* xvfb
* tmux

## Installation

Besides installing the before mentioned software just execute the steps as described as below and if some software/dependency is missing install said dependency and note it down (here). I strongly suggest working in a virtual environment for everything python related to prevent cluttering of the global workspace.

### Special Libraries

* Modified version of sqlparse (https://github.com/simkoc/sqlparse)

## Pre-Prep

You can use the racoon_installer script located in `install_racoon` to create Racoons folder-structure, a virtual environment, a host only interface and download Selenium Runner and its dependencies.
Install the database schema using the script located in `./detector/database`

### Preparation:

The first step is to 'install' the virtual machine the usecase is supposed to be run against. Those machines can be acquired from bitnami.com and we assume from here on that the VM used is a bitnami provided one even though the overall approach is not specific to bitnami provided machines. To install the corresponding machine use `install_vm.sh` in the `./install_vm/` folder - the IP may be chosen abitrarily within 192.168.56.0/24. 
	   
Wait until the script finishes (may take a while) and ensure that virtualbox now has a virtual machine registered with the state `racoon-ready`.

First the wanted use case recipe has to be selected or generated. The generation can be done by opening the Selenium IDE and recording all the steps belonging to the use case. Then saving the steps. We will refer to this use case recipe as `recipe.html` from here on.

Note: Everytime you need certain properties for making your recipe work you have to save them as a state in your VM.
E.g. running a recipe for user-login, you have to create the user in your web-shop so selenese is actually able to login a valid user.

## Detecting and Verifying WARCs using Racoon

### Running Tests:

Now you are ready for running tests. The main script for running racoon is located at `/detector/racoon.py`. In the end the database has to be checked for race condition candidates where the racoon baseline gathering (automatically done at the start) has a lower success rate than the actual test.

You have the options to run full tests based on a config file or run it directly with command line arguments.

Example Config Files can be found in `/detector/automatic_run/example_conf`. Check `./racoon config --help` for further information concerning arguments.

To perform a full test based on command-line arguments run:
`./racoon.py full [-h] [--simulate] [--relaxed-check] host user pwd database threshold root_user root_pwd vm_ip vm_name vm_state max_fuse_delay walzing_barrage_timer xpath racoon_path selenese_script_folder hit_threshold proj_name operation web_user sel_runner sel_timeout sel_speed firefox sel_receipe`

## Further functionalities of Racoon

### Analysis
We started creating a collection of debugging-tools for Racoon.

As far we created an option to directly show xdebugs that are generated during the ground data gathering.
To access this option and possible further debugging-tools run `./racoon.py analysis`.
