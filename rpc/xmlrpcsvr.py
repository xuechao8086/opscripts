#!/usr/bin/env python2.7
#coding:utf8

"""
Author:         charliezhao
Filename:       svr.py
Last modified:  2015-06-27 22:00
Description:

"""

import os
import sys
import argparse
import subprocess
import select
import signal
import time
import random

from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
from SimpleXMLRPCServer import SimpleXMLRPCDispatcher

from SocketServer import ForkingTCPServer
from SocketServer import ThreadingTCPServer

DEBUGMODE = True
#DEBUGMODE = False

try:
    import fcntl
except ImportError:
    fcntl = None




def XmlRPCServer(addr, requestHandler=SimpleXMLRPCServer,
        logRequests=True, allow_none=False, encoding=None, bind_and_activate=True, svrtype=1):
    """
    :param svrtype: 1 -> ForkingTCPServer, 2 -> ThreadingTCPServer

    """
    class XmlRPCForkServer(ForkingTCPServer,
        SimpleXMLRPCDispatcher):
        allow_reuse_address = True
        _send_traceback_header = False

        def __init__(self, addr, requestHandler,
                 logRequests, allow_none, encoding, bind_and_activate):
            self.logRequests = logRequests

            SimpleXMLRPCDispatcher.__init__(self, allow_none, encoding)
            ForkingTCPServer.__init__(self, addr, requestHandler, bind_and_activate)

            if fcntl is not None and hasattr(fcntl, 'FD_COLEXEC'):
                flags = fcntl.fcntl(self.fileno(), fcntl.F_GETFD)
                flags |= fcntl.FD_COLEXEC
                fcntl.fcntl(self.fileno(), fcntl.F_SETFD, flags)


    class XmlRPCThreadingServer(ThreadingTCPServer,
            SimpleXMLRPCDispatcher):
        allow_reuse_address = True
        _send_traceback_header = False

        def __init__(self, addr, requestHandler,
                 logRequests, allow_none, encoding, bind_and_activate):
            self.logRequests = logRequests

            SimpleXMLRPCDispatcher.__init__(self, allow_none, encoding)
            ThreadingTCPServer.__init__(self, addr, requestHandler, bind_and_activate)

            if fcntl is not None and hasattr(fcntl, 'FD_COLEXEC'):
                flags = fcntl.fcntl(self.fileno(), fcntl.F_GETFD)
                flags |= fcntl.FD_COLEXEC
                fcntl.fcntl(self.fileno(), fcntl.F_SETFD, flags)

    svrtype = 1
    if svrtype == 1:
        return XmlRPCForkServer(addr, requestHandler,
                logRequests, allow_none, encoding, bind_and_activate)
    elif svrtype == 2:
        return XmlRPCThreadingServer(addr, requestHandler,
                logRequests, allow_none, encoding, bind_and_activate)
    else:
        assert False



def _add(a, b):
    return a + b

def _multi(a, b):
    return a * b

def _echo(s):
    print 'receive {0}'.format(s)
    return s

def _cat(filename):
    with open(filename, 'r') as f:
        return f.read()

def _consume_cpu_logterm():
    random_num = 0
    while True:
        if random_num > 1024:
            random_num -= 1
        else:
            random_num += 1
    return random_num

def _consume_cpu_shortterm(s=1024*1024):
    s = s if s>0 else -s
    s = random.randint(0, s)
    even_num_count = 0
    for i in xrange(0, s):
        if i%2:
            even_num_count += 1
    return even_num_count

def parse_argument():
    parser = argparse.ArgumentParser(
            description='xmlrpc server for system administrator',
            usage='%(prog)s [options]',
            )

    parser.add_argument('-t', '--thread',
            help='thread mode',
            action='store_const', const=2)

    parser.add_argument('-f', '--fork',
            help='multiprocess fork mode, the default',
            action='store_const', const=1)

    parser.add_argument('-i', '--ip',
            help='the default ip address to use',
            type=str, default='127.0.0.1',
            metavar='ip')

    parser.add_argument('-p', '--port',
            help='the port to use',
            type=int, default=8080,
            metavar='port')

    return parser.parse_args()


if __name__ == '__main__':
    #start here....

    args = parse_argument()

    if args.thread:
        server = XmlRPCServer(addr=(args.ip, args.port),
                 requestHandler=SimpleXMLRPCRequestHandler,
                 logRequests=True,
                 svrtype=2)
    else:
        server = XmlRPCServer(addr=(args.ip, args.port),
                 requestHandler=SimpleXMLRPCRequestHandler,
                 logRequests=True,
                 svrtype=1)

    server.register_function(_add, 'add')
    server.register_function(_multi, 'multi')
    server.register_function(_echo, 'echo')
    server.register_function(_cat, 'cat')
    server.register_function(_consume_cpu_logterm, 'consume_cpu_logterm')
    server.register_function(_consume_cpu_shortterm, 'consume_cpu_shortterm')

    server.serve_forever()
