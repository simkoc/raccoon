import logging
import socket
import argparse
import sys
import time
from threading import Thread
from Queue import Queue, Empty
import traceback
import os
import subprocess

LOGGER = logging.getLogger("HQ")
LOGGER.setLevel(logging.DEBUG)
_CH = logging.StreamHandler()
_CH.setLevel(logging.DEBUG)
_FORMAT = logging.Formatter(fmt="[%(asctime)s] %(name)s (%(levelname)s) %(message)s",
                            datefmt='%d/%b/%Y:%I:%M:%S')
_CH.setFormatter(_FORMAT)
LOGGER.addHandler(_CH)
_LOCAL_THREAD_QUEUE = Queue()


# Credits to https://stackoverflow.com/a/21158235/919343
class IterableQueue():
    def __init__(self, source_queue):
        self.source_queue = source_queue

    def __iter__(self):
        while True:
            try:
                yield self.source_queue.get_nowait()
            except Empty:
                return


def check_rodger(conn):
    rodger = conn.recv(1024)
    if rodger != "OK":
        raise Exception("received bad rodger: '{}'".format(rodger))

def check_firebase(firebase, logger):
    script_path = "{}/start-single-firebase.sh".format(os.path.realpath(__file__)[0:len(os.path.realpath(__file__))-6])
    logger.info("checking if firebase-{} is still running".format(firebase[1][3]))
    if os.system("tmux ls | grep firebase-{}".format(firebase[1][3])) != 0:
        logger.info("firebase down, waiting for port to be unbound...")
        logger.info("sleep 60sec")
        time.sleep(60)
        subprocess.call([script_path, firebase[1], firebase[2], firebase[3]])
        logger.info("waiting for firebase to get ready")
        time.sleep(30)
        logger.info("firebase-{} restarted".format(firebase[1][3]))
    else:
        logger.info("firebase-{} still running".format(firebase[1][3]))

def distribute_fireorder(firebase, tc, target, logger):
    ttype = tc.split(".")[-1]
    firesolution = open(tc)
    firesolution_txt = firesolution.read()
    # LOGGER.debug("{} digitalized firesolution".format(firebase))
    firesolution.close()
    # LOGGER.debug("{} transmitting firesolution...".format(firebase))
    logger.info("sending {} ttype information".format(ttype))
    firebase.send(ttype)
    logger.info("sending firesolution")
    firebase.send(firesolution_txt)
    check_rodger(firebase)
    # LOGGER.debug("{} transmitting target coordinates...".format(firebase))
    firebase.send(target)
    check_rodger(firebase)
    # LOGGER.debug("{} preparational communication done".format(firebase))


def parse_args(args):
    parser = argparse.ArgumentParser(
        description='parameters for parallel website access')
    parser.add_argument("firebases",
                        help="ip:port of vm running firebase.py")
    parser.add_argument("tc",
                        help="the test case to run")
    parser.add_argument("target",
                        help="the ip of the target webapp")

    pargs = parser.parse_args(args)
    return pargs.tc, pargs.target, [firebase.split(":") for firebase in pargs.firebases.split(",")]


def send_fireorder(firebase, tc, target, logger=LOGGER):
    check_firebase(firebase, logger=logger)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        logger.debug("calling firebase {} on target {} with solution {}".format(
            firebase,
            target,
            tc))
        s.connect((firebase[0], int(firebase[1])))
        logger.info("FB:{} - distributing firesolution {}".format(firebase, tc))
        distribute_fireorder(s, tc, target, logger)
        logger.debug("FB:{} - distributed firesolution".format(firebase))
        s.send("FIRE")
        logger.info("FB:{} - gave fire order waiting for report...".format(firebase))
        rodger = s.recv(1024)
        logger.debug("FB:{} - receiveHQ_subd rodger: {}".format(firebase, rodger))
        if rodger == "SUCCESS":
            logger.info("FB:{} - strike was successfull".format(firebase))
            _LOCAL_THREAD_QUEUE.put(1)
        elif rodger == "FAILURE":
            logger.info("FB:{} - strike ran sel into issues".format(firebase))
        else:
            logger.info("FB:{} - strike failed".format(firebase))
    except:
        logger.error("encountered errror sending fireorder to {}".format(firebase))
        traceback.print_exc()


def HQ(args):
    tc, target, firebases = parse_args(args)
    coms = []
    for firebase in firebases:
        thread = Thread(target=send_fireorder,
                        args=(firebase, tc, target,))
        thread.start()
        coms.append(thread)
    [com.join() for com in coms]


def HQ_sub(tcs, target, firebases, logger=None):
    coms = []
    counter = 0
    for firebase in firebases:
        try:
            thread = Thread(target=send_fireorder,
                            args=(firebase, tcs[counter % len(tcs)], target, logger))
            thread.start()
            coms.append(thread)
        except:
            if logger is not None:
                logger.error("encountered error while calling {}".format(
                    firebase))
        counter = counter + 1
    [com.join() for com in coms]
    time.sleep(10)
    ret = 0
    while not _LOCAL_THREAD_QUEUE.empty():
        ret = ret + _LOCAL_THREAD_QUEUE.get()
    return ret


def HQ_sub_seq(tcs, target, firebases, count=10, logger=None):
    count = len(firebases)
    for i in range(0, count):
        if logger is not None:
            logger.info("starting sequential try no {}".format(
                i))
        com = None
        firebase = firebases[0]
        try:
            thread = Thread(target=send_fireorder,
                            args=(firebase, tcs[i % len(tcs)], target, logger))
            thread.start()
            com = thread
        except:
            if logger is not None:
                logger.error("encoutnered error while calling {".format(
                    firebase))
        com.join()

    succ = 0
    while not _LOCAL_THREAD_QUEUE.empty():
        succ = succ + _LOCAL_THREAD_QUEUE.get()
    return succ


if __name__ == '__main__':
    sys.exit(HQ(sys.argv[1:]))
