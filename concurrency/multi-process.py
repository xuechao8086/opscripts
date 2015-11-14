#!/usr/bin/python2.7
import multiprocessing
import os
import sys
import Queue
import time

def write_queue(q, obj):
    q.put(obj, True, None)
    print 'put size:', q.qsize()

def read_queue(q):
    ret=q.get(True, 1)
    print 'get size:', q.qsize()
    return ret

def producer(q):
    time.sleep(5)
    pid=os.getpid()
    with open('./multi-process.dat', 'r') as f:
        for line in f:
            print 'producer <', pid, '> is doing', line
        write_queue(q, line.strip())
    q.close()

def worker(q):
    time.sleep(5)
    pid=os.getpid()
    empty_count=0
    while True:
        try:
            task=read_queue(q)
            print 'worker <', pid, '> is doing:', task
            time.sleep(5)
        except Queue.Empty:
            empty_count+=1
            if empty_count==3:
                print 'queue is empty, quit'
                q.close()
                sys.exit(0)

def main():
    concurrence=3
    q=multiprocessing.Queue(10)
    funcs=[producer, worker]
    for i in range(concurrence-1):
        funcs.append(worker)
    for item in funcs:
        print str(item)
    nfuncs=range(len(funcs))
    processes=[]
    for i in nfuncs:
        p=multiprocessing.Process(target=funcs[i], args=(q,))
        processes.append(p)
    print 'concurrence worker is:', concurrence, 'working start'
    for i in nfuncs:
        processes[i].start()
    for i in nfuncs:
        processes[i].join()
    print 'all done'



if __name__ == '__main__':
    main()
