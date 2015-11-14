#!/usr/bin/env python2.7
#-*- coding: utf-8 -*-

"""
Author:         charliezhao
Filename:       multi-thread.py
Last modified:  2015-04-27 16:52
Description:
                
"""
import threading
import functools

from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool


def example_func(args1, args2=None):
    print 'args1 = {0}, args2 = {1}'.format(args1, args2)

def run_all(handler, args):
    pool = ThreadPool(len(args))
    res = pool.map(handler, args )
    pool.close()
    pool.join()
    return res

if __name__ == '__main__':
    #start here....
     
    args = [ (i, i+10) for i in xrange(0, 10) ]

    run_all(functools.partial(example_func, args2='xuechaozhao'),
            args)
     
