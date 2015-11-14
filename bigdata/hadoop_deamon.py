#! /usr/bin/python
import os,sys
import threading

def getfilelst():
	f_total = open("total_file")
	f_succ  = open("succ")
	succ_files = [one.strip() for one in f_succ.readlines()]
	ret = []
	for file in f_total.readlines():
		if file.strip() in succ_files:
			continue
		ret.append(file[1:])
	f_total.close()
	f_succ.close()
	return ret

def getfile(filename):
	filename = filename.strip()
	cmd = 'rsync @10.151.18.111::nat2%s ./' % filename
	os.system(cmd)
	fname = filename.split('/')[-1]
	os.system('tar zxvf ./%s'% fname)
	fname2 = fname.split('.')[0]
	return filename.split('/')[-2], fname2


def donefile(filename):
	filename = filename.strip()
	fname = filename.split('/')[-1]
	os.system('rm -f ./%s'% fname)
	fname2 = fname.split('.')[0]
	os.system('rm -fr ./%s'% fname2)

	f = open("./succ","a")
	f.write("."+filename+'\n')
	f.close()


def gzdir(dirname):
	cmd = 'rm -fr ./%s/idc=ca/' % dirname
	os.system(cmd)
	cmd = "find ./%s -name '*.log'|xargs gzip" % dirname
	os.system(cmd)



def handle():
	for filename in getfilelst():
		logid, fname = getfile(filename)
		datestr = fname[0:8]
		gzdir(fname)
		hadoopcmd = 'find ./%s -name "*.gz"|xargs -I{} hadoop fs -put {} /database/mmdata/log_%s/ds=%s/' % (fname, logid, datestr)
		print hadoopcmd
		if os.system(hadoopcmd) == 0:
			donefile(filename)


class worker(threading.Thread):
    def __init__(self, begin, end, filelst):
        super(worker,self).__init__()
        self.begin = begin
        self.end = end
        self.filelst = filelst
    
    def run(self):
        for i in range(self.begin, self.end):
            logid, fname = getfile(self.filelst[i])
            datestr = fname[0:8]
            gzdir(fname)
            hadoopcmd = 'find ./%s -name "*.gz"|xargs -I{} hadoop fs -put {} /database/mmdata/log_%s/ds=%s/' % (fname, logid, datestr)
            print hadoopcmd
            if os.system(hadoopcmd) == 0:
                 donefile(self.filelst[i])

def handle_multithread(tnum):
    filelst = getfilelst()
    print len(filelst)
    perreq = int( len(filelst)/tnum )

    threads = []
    for i in range(0, len(filelst), perreq):
        begin = i
        end = i + perreq
        if end >= len(filelst):
            end = len(filelst)

        t = worker(begin,end,filelst)
        t.start()
        threads.append(t)

    for t in threads:
        t.join(1)

if __name__ == "__main__":
	#handle()
    handle_multithread(int(sys.argv[1]))




