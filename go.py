#!/usr/bin/env python2.7
#coding:utf8

"""
Author:         charliezhao
Filename:       go.py
Last modified:  2015-03-07 01:15
Description:
                
"""
import pexpect
import traceback
import sys
import re
import struct
import fcntl
import termios
import signal
import sys

def ssh_command(user, host, password):
    need_newkey = 'yes/no'
    need_pass = 'assword:'
    child = pexpect.spawn('ssh -q -l {user} {host}'.format(user=user, host=host))
    ret1 = child.expect([need_pass, need_newkey, pexpect.TIMEOUT])
    if ret1 == 0:
        child.sendline(password)
        return child
    if ret1 == 1:
        child.sendline('yes')
        ret2 = child.expect([need_pass, need_newkey, pexpect.TIMEOUT])
        if ret2 == 0:
            child.sendline(password)
            return child
        if ret2 == 1:
            child.sendline('yes')
            ret3 = child.expect([need_pass, pexpect.TIMEOUT])
            if ret3 == 0:
                child.sendline(password)
                return child
            if ret3 == 1:
                print 'Error Timeout 3!'
        if  ret2 == 2:
            print 'Error Timeout 2!'
    if ret1 == 2:
        print 'Error Timeout 1!'
    return None
    

def main(hostname, user=None, password=None):
    if re.compile("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}").match(hostname) == None:
        print "{name} error".format(name=hostname)
    else:
        host = hostname
    user = "charlie"
    if sys.argv[-1] == "root":
        user = "charlie"
    global child
    child = ssh_command(user, host, password)

    def sigwinch_passthrough(sig, data):
        s = struct.pack("HHHH", 0, 0, 0, 0)
        a = struct.unpack("hhhh", fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ, s))
        global child
        child.setwinsize(a[0], a[1])
    signal.signal(signal.SIGWINCH, sigwinch_passthrough)
    sigwinch_passthrough(None, None)
    child.interact()
    child.expect(pexpect.EOF)
    print child.before

def usage():
    print sys.argv[0], '<hostname#172.16.183.128> <password> <user#charlie>'
    sys.exit(-1)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        usage()
    try:
        ip = sys.argv[1]
        password = sys.argv[2]
        user = sys.argv[3]

        main(ip, user, password)
    except Exception, e:
        traceback.print_exc()
