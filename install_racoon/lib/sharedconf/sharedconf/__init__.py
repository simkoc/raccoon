from ConfigParser import ConfigParser
from attrdict import AttrDict
import six
import os.path

BOOLEAN_STATES = {'1': True, 'yes': True, 'true': True, 'on': True,
                  '0': False, 'no': False, 'false': False, 'off': False}


class Config(AttrDict):

    def __init__(self, *args, **kwargs):
        super(Config, self).__init__(*args, **kwargs)

    def __repr__(self):
        return six.u('Config({contents})').format(
            contents=super(AttrDict, self).__repr__()
        )

    def getint(self, key):
        return int(self[key])

    def getfloat(self, key):
        return float(self[key])

    def getboolean(self, key):
        return BOOLEAN_STATES[self[key].lower()]


def load_cfg(fn):
    
    if not os.path.isfile(fn):
        raise IOError("{} not found".format(fn))

    cfg_p = ConfigParser()
    cfg_p.read(fn)
    
    conf = Config()

    for sect in cfg_p.sections():
        s_conf = Config()

        conf.setdefault(sect, s_conf)

        for opt in cfg_p.options(sect):
            conf[sect].setdefault(opt, cfg_p.get(sect, opt))

    return conf


def merge(glob, user):
    # For conflicting keys, the right dict's value will be preferred
    return glob + user
