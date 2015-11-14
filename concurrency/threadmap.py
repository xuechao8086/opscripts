#!/usr/bin/env python2.7
#-*- coding: utf-8 -*-

"""
Author:         charliezhao
Filename:       thread.py
Last modified:  2015-04-07 19:13
Description:
                
"""

from __future__ import print_function
import threading
from multiprocessing.dummy import Pool as ThreadPool  
import time
import sys

safe_print_lock = threading.Lock()
def safe_print(*args, **kwargs):   
    with safe_print_lock:    
        now = time.strftime("%H:%M:%S")
        now_prefix = '[%s]' % (now)    
        print(now_prefix, *args, **kwargs)
        sys.stdout.flush()  


def run_all(handler, args, max_thread_num=50): 
    thread_num = len(args)     
    if thread_num > max_thread_num:   
        thread_num = max_thread_num 
    safe_print("handler(%s), len(args)(%d), max_thread_num(%d) thread_num(%d)" % (str(handler), len(args), max_thread_num, thread_num))
    pool = ThreadPool(thread_num)
    results = pool.map(handler, args)
    pool.close()
    pool.join()
    return results

def func1(args):
    safe_print(args)

if __name__ == '__main__':
    #start here....
    run_all(func1, (1, 2, 3, 4))   
     
     
