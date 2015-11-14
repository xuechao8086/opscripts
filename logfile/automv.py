#!/usr/bin/env python2.7
#coding:utf8

"""
Author:         charliezhao
Filename:       automv.py
Last modified:  2015-01-29 15:53
Description:

"""
import sys
import os
import time
import shutil

def process(filename):
    if not os.path.isfile(filename):
        print '{name} not a file'.format(name=filename) 
        return -1
    
    special_dir=('/'  '/home'  '/home/charlie'  '/home/charlie/bin'  '/home/charlie/sbin'  '/home/charlie/etc'  '/home/charlie/lib'  '/home/charlie/data'  '/usr'  '/usr/local'  '/usr/local/charlie'  '/usr/local/charlie/bin'  '/usr/local/charlie/sbin'  '/usr/local/charlie/etc'  '/usr/local/charlie/lib' '/data1/charlie/data' '/data/charlie/data')
    if os.path.dirname(filename) in special_dir:
        print '{name} in special_dir'.format(name=filename)
        return -2
    
    filename_bak='{name}.{date}'.format(name=filename, date=time.strftime('%Y%m%d%H%M%S', time.localtime()) )
    print filename_bak
#real copy
    shutil.copy(filename, filename_bak) 

def usage():
    print sys.argv[0], '[filename1] [filename2] [filename3]......'
    print 'Note: use to backup file at the current directory'

if __name__ == '__main__':
    if len(sys.argv)==1:
        usage()
        sys.exit(-1)

    for filename in sys.argv[1:]:
        process(filename)
