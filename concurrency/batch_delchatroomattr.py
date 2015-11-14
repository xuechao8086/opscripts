#!/usr/bin/env python2.7
#coding:utf8

"""
Author:         charliezhao
Filename:       deamon.py
Last modified:  2015-03-03 15:29
Description:
"""

import sys
import os
import logging
import time
import commands
import multiprocessing
import glob


def main():
    os.chdir('/home/charlie/data/chatroom_clean/100wHeadTest')
    LOGFILE = './{filename}.log'.format(filename=sys.argv[0])
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(filename)s:%(lineno)d %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S', filename=LOGFILE, filemode='a+')

    logging.debug('{proc} begin'.format(proc=sys.argv[0]))
    filenames = glob.glob('./x[a-a][a-z]')
    pool = multiprocessing.Pool( processes=10 )
    for filename in filenames:
        pool.apply_async(batchExecute, (filename,))
    pool.close()
    pool.join()
    logging.debug('{proc} end'.format(proc=sys.argv[0]) )

 
def batchExecute(filename):
    logging.debug('{filename} begin'.format(filename=filename))
    print filename
    cmd = './batch_delchatroomattr {filename}'.format(filename=filename)
    rtn, output = commands.getstatusoutput(cmd)
    logging.info('{cmd} rtn:{rtn} output:{output}'.format(cmd=cmd, rtn=rtn, output=output))
    logging.debug('{filename} end'.format(filename=filename))

   
def daemonize(stdout='/dev/null', stderr=None, stdin='/dev/null', pidfile=None, startmsg='started with pid %s'):
    '''
      This forks the current process into a daemon. 
      The stdin, stdout, and stderr arguments are file names that 
      will be opened and be used to replace the standard file descriptors 
      in sys.stdin, sys.stdout, and sys.stderr. 
      These arguments are optional and default to /dev/null. 
      Note that stderr is opened unbuffered, 
      so if it shares a file with stdout then interleaved output may not appear in the order that you expect. 
    '''

    sys.stdout.flush()
    sys.stderr.flush()
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError, e:
        print >> sys.stderr, 'fork #1 failed: %d(%s)'% (e.errno, e.strerror)
        sys.exit(1)
    
    os.chdir('/')
    os.setsid()
    os.umask(0)
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError, e:
        print >> sys.stderr, 'fork #1 failed: %d(%s)'% (e.errno, e.strerror)
        sys.exit(1)
   
    if not stderr:
        stderr = stdout
    si = file(stdin, 'r')
    so = file(stdout, 'a+')
    se = file(stderr, 'a+', 0)
    pid = str( os.getpid() )
    if pidfile:
        with open(pidfile, 'w+') as f:
            f.write('%s\n'% pid)
    os.dup2( si.fileno(), sys.stdin.fileno() )
    os.dup2( so.fileno(), sys.stdout.fileno() )
    os.dup2( se.fileno(), sys.stderr.fileno() )
    
if __name__ == '__main__':
    daemonize( stdout='/home/charlie/log/error/{name}.log'.format(name=sys.argv[0]) )
    main()
