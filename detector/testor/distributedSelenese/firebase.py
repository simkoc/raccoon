import socket
import logging
import sys
import time
import os
from random import randint
from subprocess import call
import argparse

HOME = os.getenv('HOME')
GUN_ENPLACEMENTS = 5
HOST = ''
MAX_FUSE_DELAY = sys.argv[2]
WALZING_BARAGE_TIMER = sys.argv[3]
TARGET_WINDOW_HEIGHT = "2048"
TARGET_WINDOW_WIDTH = "2048"
FIRESOLUTION_PATH_EXMPL = "{}/.racoon/firebases/firesolution-{{}}.{{}}".format(HOME)
#MUNITIONS_DEPOT = "{}/.racoon/firebases/firefox/firefox".format(HOME)
MUNITIONS_DEPOT = "/usr/bin/firefox"
GUN_PLACEMENT = "{}/firebases/selenese-runner.jar".format(HOME)
ACTION_LOG_FOLDER = "/{}/.racoon/firebases/".format(HOME)
LOGGER = logging.getLogger("firebase")
LOGGER.setLevel(logging.DEBUG)
_CH = logging.StreamHandler()
_CH.setLevel(logging.DEBUG)
_FORMAT = logging.Formatter(fmt="[%(asctime)s] %(name)s (%(levelname)s) %(message)s",
                            datefmt='%d/%b/%Y:%I:%M:%S')
_CH.setFormatter(_FORMAT)
LOGGER.addHandler(_CH)


def receive_firesolution(conn):
    firesolution = ""
    ttype = conn.recv(4)
    if ttype not in ['html', 'side']:
        raise Exception("unexpected selenese script {}".format(ttype))
    LOGGER.info("received firesolution type {}".format(ttype))
    while True:
        data = conn.recv(4096)
        LOGGER.debug("received partial firesolution")

        if not data:
            break

        firesolution += data

        if len(data) < 4096:
            break

    return firesolution, ttype


def distribute_firesolution(data, path):
    file = open(path, 'w')
    file.write(data)
    file.close()


def commence_firesolution(coordinates, port, action_time, path):
    log_file = "{}/{}-gun-position-{}.log".format(ACTION_LOG_FOLDER,
                                                  action_time,
                                                  port)
    # I hereby propose this hack for the uglies fix in history award
    # if all firebases request a selense connection at the same time
    # it results in crashes for some. I thus delay the connection
    # request by the last digit of the assigned port number
    time.sleep(port % 10)
    LOGGER.debug("selenese firing after {} delay".format(port % 10))
    with open(log_file, 'w') as log:
        ret = call(["java",
                    "-jar", GUN_PLACEMENT,
                    "--firefox", MUNITIONS_DEPOT,
                    "--set-speed", WALZING_BARAGE_TIMER,
                    "--height", TARGET_WINDOW_HEIGHT,
                    "--timeout", MAX_FUSE_DELAY,
                    "--width", TARGET_WINDOW_WIDTH,
                    "--screenshot-on-fail", "{}/failshots/".format(ACTION_LOG_FOLDER),
                    "--baseurl", "http://{}".format(coordinates),
                    path],
                   stdout=log,
                   stderr=log)
        return ret


def firebase_loop(PORT):
    SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    SOCKET.bind((HOST, PORT))
    try:
        while True:
            SOCKET.listen(1)
            LOGGER.info("firebase ready for orders on port {}".format(PORT))
            LOGGER.info("running with max_fuse_delay of {}ms and walzing_barrage_timer of {}ms".format(MAX_FUSE_DELAY, WALZING_BARAGE_TIMER))
            conn, addr = SOCKET.accept()
            try:
                LOGGER.info("receive communication from HQ")
                firesolution, ttype = receive_firesolution(conn)
                LOGGER.info("received firesoultion")
                path = FIRESOLUTION_PATH_EXMPL.format(PORT, ttype)
                distribute_firesolution(firesolution, path)
                LOGGER.info("distributed firesolution")
                conn.send("OK")
                coordinates = conn.recv(1024)
                LOGGER.info("received target coordinates")
                conn.send("OK")
                fire_order = conn.recv(1024)
                LOGGER.info("received fire orders")
                if fire_order == "FIRE":
                    LOGGER.info("commencing barrage")
                    action_time = time.strftime('%Y%m%d%H%M%S')
                    LOGGER.info("gun firing...")
                    ret = commence_firesolution(coordinates, PORT,
                                                action_time, path)
                    if ret == 0:
                        conn.send("SUCCESS")
                    else:
                        conn.send("FAILURE")
                    LOGGER.info("barrage finished")
                elif fire_order == "ABORD":
                    LOGGER.info("barrage cancelled")
                    pass
                else:
                    raise Exception("unknown order: '{}'".format(fire_order))
            finally:
                conn.close()
    finally:
        SOCKET.close()


if __name__ == '__main__':
    sys.exit(firebase_loop(int(sys.argv[1])))
