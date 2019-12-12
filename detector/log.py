'''
Created on 14 Sep 2010

@author: gianko
'''

import logging
from datetime import datetime

LEVELS = [logging.INFO, logging.INFO, logging.DEBUG]


LEVEL = logging.DEBUG
# LEVEL = logging.INFO


def getdebuglogger(component):
    # create logger
    logger = logging.getLogger(component)
    logger.setLevel(LEVEL)

    #create file handler and set level to debug
    now = datetime.now()
    current_time = str(now.strftime("%Y%m%d%H%M%S"))

    fh = logging.FileHandler("racoon-main-{}.log".format(current_time))
    fh.setLevel(LEVEL)    
    
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(LEVEL)
    
    # create formatter
    formatter = logging.Formatter(fmt="[%(asctime)s] %(name)s (%(levelname)s) %(message)s",
                                  datefmt='%d/%b/%Y:%I:%M:%S')
    
    # add formatter to ch and fh
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)

    # add ch and fh to logger
    logger.addHandler(ch)
    logger.addHandler(fh)

    
    return logger
