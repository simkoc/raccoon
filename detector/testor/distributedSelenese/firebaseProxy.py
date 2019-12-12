#!/usr/bin/env python

import socket
import argparse
import sys
import logging

LOGGER = logging.getLogger("Proxy")
LOGGER.setLevel(logging.DEBUG)
_CH = logging.StreamHandler()
_CH.setLevel(logging.DEBUG)
_FORMAT = logging.Formatter(fmt="[%(asctime)s] %(name)s (%(levelname)s) %(message)s",
                            datefmt='%d/%b/%Y:%I:%M:%S')
_CH.setFormatter(_FORMAT)
LOGGER.addHandler(_CH)


HOST = ''


def firebase_proxy(port, target_ip, target_port):
    SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    SOCKET.bind((HOST, port))
    LOGGER.info("started proxy on port {} for target {}:{}".format(port, target_ip, target_port))
    try:
        while True:
            SOCKET.listen(1)
            conn, addr = SOCKET.accept()
            LOGGER.info("incoming connection from {}".format(addr))

            firebase_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            firebase_socket.connect((target_ip, target_port))
            LOGGER.info("connected to forward firebase")
            try:
                firesolution = receive_firesolution(conn)
                firebase_socket.send(firesolution)
                rodger = firebase_socket.recv(1024)
                conn.send(rodger)
                LOGGER.info("forwarded firesolution and received rodger: {}".format(rodger))
                    
                coordinates = conn.recv(1024)
                firebase_socket.send(coordinates)
                rodger = firebase_socket.recv(1024)
                conn.send(rodger)
                LOGGER.info("forwarded coordinates and received rodger: {}".format(rodger))
                
                fire_order = conn.recv(1024)
                firebase_socket.send(fire_order)
                result = firebase_socket.recv(1024)
                conn.send(result)
                LOGGER.info("forwarded fireorder and received rodger: {}".format(result))
            finally:
                conn.close()
                LOGGER.info("communication with firebase done")
    finally:
        SOCKET.close()
        LOGGER.info("proxy now dead!")


def parse_args(args):
    parser = argparse.ArgumentParser(
        description='parameters for the proxy')
    parser.add_argument("port",
                        help="the port to run the proxy on")
    parser.add_argument("firebase",
                        help="ip:port of the firebase to proxy for")
    pargs = parser.parse_args(args)
    return int(pargs.port), pargs.firebase.split(":")[0], int(pargs.firebase.split(":")[1])


def main(args):
    port, firebase_ip, firebase_port = parse_args(args)
    firebase_proxy(port, firebase_ip, firebase_port)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
    
