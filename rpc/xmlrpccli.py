#!/usr/bin/env python2.7
#coding:utf8

"""
Author:         charliezhao
Filename:       rpccli.py
Last modified:  2015-06-28 10:14
Description:
                
"""

import xmlrpclib
import threading

class CliSvr(object):
    pass


if __name__ == '__main__':
    svr = xmlrpclib.ServerProxy("http://localhost:8080")
    print svr.add(2, 3)
    print svr.multi(2, 3)
    print svr.consume_cpu_shortterm()
    print svr.echo('charliezhao xmlrpc echo') 
     
