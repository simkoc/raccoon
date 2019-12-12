# Shared Configuration Library

This library allows to share global and user configuration of our tool chain. 


## Install

`pip install .`

## Update

`pip install --upgrade .`


## File Format

This is an example of the file format (see `test/global.cfg.example`):

```
[postgresql]
host=127.0.0.1
port=5432
username=dbuser
password=dbpassword
database=deepmodel


[neo4j]
# put server location here
host=localhost

# put username here
username=neo4j

# put password here
database=password


[php]
session_save_path=/opt/something
xdebug_save_path=/tmp/

[virtualbox]
ip=192.168.56.101

[bitnami]
root=bitnami
password=bitnami
```

`postgresql`, `neo4j`, `php`, `virtualbox`, and `bitnami` are called sections. Key-value pairs are collect options.

## Load Configuration from Python (module shareconf)

Install the library using:

```bash
$ cd lib/sharedconf

$ pip install .
```

Then, you can use the library from python as follows:

```python
import sharedconf

g_cfg = sharedconf.load_cfg("test/global.cfg.example")

print g_cfg.bitnami.root        # this returns the string bitnami
print g_cfg["bitnami"]["root"]  # this returns the string bitnami
print g_cfg.bitnami.password    # this returns the string bitnami

# This can be a user-provided configuration file. We want to merge
# this configuration with the global stored in global.cfg.example
u_cfg = {"bitnami":{"root":"newuser"}}

cfg = sharedconf.merge(g_cfg, u_cfg)

print cfg.bitnami.root        # this returns the string newuser
print cfg["bitnami"]["root"]  # this returns the string newuser
print cfg.bitnami.password    # this returns the string bitnami 
                              # (inherited from c_cfg)
```

## Load Configuration from Bash (bash script shareconf.sh)

The same configuration file can be used from bash. As opposed to the python library, our bash library does not support configuration merging.

To use `test/global.cfg.example` from bash, do as follows:

```bash
$ cd lib/sharedconf

$ source sharedconf.sh test/global.cfg.example

$ echo ${bitnami[root]}
bitnami

$ echo ${bitnami[password]}
bitnami
```

