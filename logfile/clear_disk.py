#!/usr/bin/python
#-*- coding=utf-8 -*-
#author wokinchen

import socket,time,shutil,filecmp,tarfile,signal,stat,os,glob,mimetypes,sys,subprocess

bin_path = '/home/charlie'
compress_type = 'gz'
thenices=-20

def get_now_time(format='%Y-%m-%d %H:%M:%S'):
    tm = time.strftime(format,time.localtime(time.time()))
    return tm

upload_conf = bin_path+"/upload/wxclear.conf"
conf_file = bin_path+"/etc/wxclear.conf"
cleared_log = bin_path+"/log/beencleared_"+get_now_time('%Y%m')+".log"
log_file = bin_path+"/log/clear_"+get_now_time('%Y%m')+".log"

pid_file_name = '/tmp/clear_disk.pid'

limit_time = 2
limit_size = 6

fd_log = open(log_file,"a")
fd_cleared_log = open(cleared_log, "a")
begin_time = time.time()

conf_list = []
export_rules = []

def log(log_str):
    global fd_log
    tm = get_now_time()
    fd_log.write('[%s] %s\n' % (tm,log_str))

def write_cleared_log(path,work_type,work_id):
    global fd_cleared_log
    work_date = get_now_time()
    work_id = str(work_id)
    fd_cleared_log.write(':'.join([work_date,path,work_type,work_id]) + "\n")
    #print "write to upload_flog:"+cleared_log+" "+'"'.join([work_date,path,work_type,work_id])
    
def check_disk():
    global limit_time,limit_size
    VAL_TEST = 85
    disk_name = ['/data','/data1','/','/usr/local']
    used_name = ['DISK_USED_DATA','DISK_USED_DATA1','DISK_USED_ROOT','DISK_USED_USR']
    used_disk = {}
    for i in xrange(4):
        if os.path.exists(disk_name[i]):
            disk = os.statvfs(disk_name[i])
            used_disk[used_name[i]] = int(100 - float(disk.f_bavail)/float(disk.f_blocks)*100)
        else:
            used_disk[used_name[i]] = -1
    print used_disk

    if used_disk['DISK_USED_ROOT'] >= VAL_TEST:
        limit_time = 5
        limit_size = 7
        log("/ used more than %d%%" % VAL_TEST)
    elif used_disk['DISK_USED_USR'] >= VAL_TEST:
        limit_time = 5
        limit_size = 8
        log("/usr/local used more than %d%%" % VAL_TEST)
    elif used_disk['DISK_USED_DATA'] >= VAL_TEST or used_disk['DISK_USED_DATA1'] >= VAL_TEST:
        limit_time = 5
        limit_size = 9
        log("/data used more than %d%%" % VAL_TEST)
    return 0

def load_config():
    global conf_file,upload_conf,limit_time,conf_list, export_rules

    if not os.path.isfile(upload_conf):
        log("%s not exists" % upload_conf)
    elif not os.path.isfile(conf_file):
        shutil.copy2(upload_conf,conf_file)
        log("conf_file not exist, copy from upload")
    elif not filecmp.cmp(upload_conf,conf_file):
        shutil.copy2(conf_file,upload_conf+'.old')
        shutil.copy2(upload_conf,conf_file)
        log("configuration file has been updated")

    if not os.path.isfile(conf_file):
        log("configuration file "+conf_file+" does not exist")
        return -1

    try:
        filter_list = ['/','/lib/','/usr/local/','/usr/lib','/sbin/','/bin/','/usr/bin/','/usr/sbin/','/usr/local/bin/','/usr/local/sbin/','/data/charlie/']

        fd_conf_file = open(conf_file)
        lines_conf_file = fd_conf_file.readlines()
        fd_conf_file.close()

        for line in lines_conf_file:
            line = line.strip()
            #load export rules 
            if line.startswith('#EXPORT'):
                rules = line.split()
                if len(rules) == 2:
                    export_rules.append(rules[1])

            elif line.startswith('#') :
                continue
            line = line.split()
            if len(line) < 9:
                continue

            confs = {}
            confs['opt'] = line[0]
            confs['param'] = line[limit_time-1]#mmin
            confs['param2'] = line[5]#size
            confs['param3'] = line[6]#total_limit
            confs['dir'] = line[2]
            confs['file'] = line[3]
            confs['subtree'] = line[7]
            confs['id'] = line[8]

            if confs['dir'] in filter_list:
                log("clear configuration contains dangerous path")
                continue
            if confs['file'].find('/') != -1:
                log("filename does not meet specifications, including dangerous characters")
                continue
            if  not confs['dir'].endswith('/'):
                log(confs['dir']+":path does not meet specification,plese add '/' to the end of the path")
                continue

            conf_list.append(confs)
    except Exception, e:
        print str(e)
        log("read configuration file filed")
        return -1
        
    return 0
    
def get_param2(param):
    if param.endswith('M'):
        param = param[:-1]
        param = int(param)*1024
    elif param.endswith('G'):
        param = param[:-1]
        param = int(param)*1048576
    elif param.endswith('k'):
        param = param[:-1]
        param = int(param)
    else:
        param = int(param)
    return param

def check_files(filenames,mmin,size,del_regular,softflag):
    namelist = []
    for fullname in filenames:
        file_stat = {}
        fullname = fullname.strip()
        if fullname == "" or fullname is None:
            continue;
        if del_regular and not os.path.isfile(fullname):
            continue
        if softflag==0 and os.path.islink(fullname):
            log("%s is softlink" % fullname)
            continue

        try:
            (imode, iino, idev, inlink, iuid, igid, isize, iatime, imtime, ictime) = os.stat(fullname)
            nowtime = time.time()

            if (nowtime - imtime)/60 <= int(mmin):
                #print str((nowtime-imtime)/60)+" <= "+str(mmin)
                continue

            if int(isize/1024) < size:
                #print str(isize/1024) < str(size)
                continue

            file_stat['size'] = isize
            file_stat['mtime'] = imtime
            file_stat['name'] = fullname
            file_stat['uid'] = iuid
            file_stat['gid'] = igid
            file_stat['mode'] = imode
            namelist.append(file_stat)
        except Exception,e:
            print str(e)
            log("check file %s failed : %s" % (fullname,str(e)))
            if os.path.islink(fullname) and not os.path.exists(os.readlink(fullname)):
                file_stat['size'] = 0
                file_stat['mtime'] = -1
                file_stat['name'] = fullname
                file_stat['uid'] = -1
                file_stat['gid'] = -1
                file_stat['mode'] = stat.S_IXOTH | stat.S_IWOTH
                namelist.append(file_stat)
        
    return namelist

def find_file(root,isrecursion=True,mmin=0,size='0k',filepattern='',regular=False,softflag=1):
    size = get_param2(size)
    filepattern = filepattern.replace("\\n","\n")
    filenames = glob.glob(os.path.join(root,filepattern))
    namelist = []
    namelist.extend(check_files(filenames,mmin,size,regular,softflag))
    if not isrecursion:
        return namelist 

    for dirpath,dirnames,filenames in os.walk(root):
        for dirname in dirnames:
            if os.path.islink(os.path.join(dirpath,dirname)):
                continue
            filenames = glob.glob(os.path.join(dirpath,dirname,filepattern))
            namelist.extend(check_files(filenames,mmin,size,regular,softflag))
    return namelist

def delete_file_by_range(confs):
    global limit_size
    log("Delete by range")
    fulllogpath = os.path.join(confs['dir'],confs['file'])
    
    subtree = False
    softflag = 1
    if confs['subtree'] == "yes":
        subtree = True
    if int(confs['param3']) == 0:
        log("Total limit not define, Exit!")
        return 0
    if confs['dir'] == '/home/charlie/upload/' and limit_size == 8:
        log("/home/charlie/upload/ in dir, Exit!")
        return 0
    
    softflag_dirs = ['/home/charlie/upload/','/home/charlie/backup/','/home/charlie/tmp/']
    if confs['dir'] in softflag_dirs:
        softflag = 0
    
    rangemmin = 10

    total_limit = int(confs['param3']) * 1024
    files_list = find_file(root=confs['dir'],isrecursion=subtree,mmin=rangemmin,size='1024k',filepattern=confs['file'],regular=True,softflag=softflag)
    files_list.sort(cmp=file_cmp)
    #print files_list

    if len(files_list) > 0:
        log("will delete_by_range %d files" % len(files_list))

    mysum = sum([int(file_stat['size']) for file_stat in files_list])

    for file_stat in files_list:
        try:
            name = file_stat['name']
            if mysum < total_limit:
                break
            if os.path.isfile(name):
                os.remove(name)
                mysum -= int(file_stat['size'])
                print "remove file "+name
            elif os.path.isdir(name) and not os.listdir(name):
                os.rmdir(name)
                print "remove dir "+name
            elif os.path.islink(name) and not os.path.exists(os.readlink(name)):
                os.remove(name)
                print "remove broken link file "+name
            else:
                continue

            write_cleared_log(file_stat['name'],'delete_by_range',file_stat['uid'])
        except Exception,e:
            print str(e)
            log("Delete_by_range %s failed : %s" % (fulllogpath,str(e)))

#    if sum <= total_limit:
#        log("No files to delete %s" % fulllogpath)
#        return 0;

    log("Delete_by_range %s complete" % fulllogpath)
    return 0

def file_cmp(file1,file2):
    if file1['mtime'] == file2['mtime']:
        return 0
    elif file1['mtime'] < file2['mtime']:
        return -1
    else:
        return 1

def delete_file(confs):
    print "Delete"
    subtree = False
    softflag = 1
    fulllogpath = os.path.join(confs['dir'],confs['file'])

    if confs['subtree'] == "yes":
        subtree = True
    softflag_dirs = ['/home/charlie/upload/','/home/charlie/backup/','/home/charlie/tmp/']
    if confs['dir'] in softflag_dirs:
        softflag = 0
    if int(confs['param2']) == 0:
        files_list = find_file(root=confs['dir'],isrecursion=subtree,mmin=confs['param'],filepattern=confs['file'],regular=False,softflag=softflag)
    else:
        files_list = find_file(root=confs['dir'],isrecursion=subtree,mmin=confs['param'],size=confs['param2']+'k',filepattern=confs['file'],regular=False,softflag=softflag)
    
    if len(files_list) == 0:
        log("No files to delete %s" % fulllogpath)
        return 0;

    if len(files_list) > 0:
        log("will delete %d files" % len(files_list))
    for file_stat in files_list:
        try:
            name = file_stat['name']
            if os.path.isfile(name):
                os.remove(name)
                print "remove file "+name
            elif os.path.isdir(name) and not os.listdir(name):
                os.rmdir(name)
                print "remove dir "+name
            elif os.path.islink(name) and not os.path.exists(os.readlink(name)):
                os.remove(name)
                print "remove broken link file "+name
            else:
                continue
            write_cleared_log(name,'delete',file_stat['uid'])
        except Exception,e:
            print str(e)
            log("Delete %s failed : %s" % (fulllogpath,str(e)))
                    
    log("Delete %s complete" % fulllogpath)
    return 0

def real_gzip(compress_type,file_stat,timeout):
    starttime = time.time()
    gzfile = '.'.join([file_stat['name'],compress_type])

    if compress_type == 'gz':
        cmd = "nice -n 19 gzip %s" % file_stat['name']
    elif compress_type == 'bz2':
        cmd = "nice -n 19 bzip2 -z %s" % file_stat['name']

    popenret = subprocess.Popen(args=cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    print "waiting for gzip"
    try:
        while popenret.poll() is None:
            time.sleep(1)
            if int(time.time()) - int(starttime) > int(timeout):
                os.kill(popenret.pid,signal.SIGKILL)
                os.rename(file_stat['name'],gzfile)
                log("%s compress outtime,rename directly" % file_stat['name'])
                break
        
        if popenret.poll() == 0:
            try:
                os.chown(gzfile,file_stat['uid'],file_stat['gid'])
                os.chmod(gzfile,file_stat['mode'])
                write_cleared_log(file_stat['name'],compress_type,file_stat['uid'])
            except Exception,e:
                print e
        elif os.path.isfile(gzfile) and os.path.isfile(file_stat['name']):
            os.remove(gzfile)
            os.rename(file_stat['name'],gzfile)
            log("%s compress error,rename directly" % file_stat['name'])

        if os.path.isfile(file_stat['name']):
            os.remove(file_stat['name'])

    except Exception,e:
        try:
            os.kill(popenret.pid,signal.SIGKILL)
            os.remove(file_stat['name'])
        except:
            pass
        log("compress % failed : %s" % (gzfile,e))

def gzip_file(confs):
    global begin_time,thenices,compress_type
    thenices = os.nice(19-thenices)
    timeout = 1800
    print compress_type
    fulllogpath = os.path.join(confs['dir'],confs['file'])
    subtree = False
    softflag = 1
    if confs['subtree'] == "yes":
        subtree = True
    files_list = find_file(root=confs['dir'],isrecursion=subtree,mmin=confs['param'],size=confs['param2']+'k',filepattern=confs['file'],regular=False,softflag=softflag)
    if len(files_list) == 0:
        log("No files to %s %s" % (compress_type,fulllogpath))
        return 0

    if len(files_list) > 0:
        log("will compress %d files" % len(files_list))
    for file_stat in files_list:
        try:
            gzfile = file_stat['name']+'.'+compress_type

            (guesstyoe,guessencode) = mimetypes.guess_type(file_stat['name'])
            if guessencode == 'gzip' or guesstyoe == 'application/x-bzip' or guessencode == 'bzip2':
                continue
            if os.path.isfile(gzfile):
                os.remove(gzfile)
                print "remove zip file %s" % gzfile
            else:
                now_time = time.time()
                if int(now_time-begin_time) >= 1800:
                    print now_time-begin_time
                    break
            if compress_type == 'gz':
                cmd = "nice -n 19 gzip %s" % file_stat['name']
                s = subprocess.Popen(args=cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                ret = s.stdout.read() 
                print ret
            elif compress_type == 'bz2':
                cmd = "nice -n 19 bzip2 -z %s" % file_stat['name']
                s = subprocess.Popen(args=cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                ret = s.stdout.read() 
                print ret

            os.chown(gzfile,file_stat['uid'],file_stat['gid'])
            os.chmod(gzfile,file_stat['mode'])

            real_gzip(compress_type,file_stat,timeout)
            print " ".join([compress_type,"file",file_stat['name']])
            write_cleared_log(file_stat['name'],compress_type,file_stat['uid'])
        except Exception,e:
            print str(e)
            log("%s %s failed : %s" % (compress_type,fulllogpath,str(e)))
    log("%s %s complete" % (compress_type,fulllogpath))
    return 0

def clear_file(confs):
    fulllogpath = os.path.join(confs['dir'],confs['file'])
    try:
        files_list = find_file(root=confs['dir'],isrecursion=False,size=confs['param2']+'k',filepattern=confs['file'],regular=True)
    except Exception,e:
        print str(e)
        log("search filelist to be cleared failed")
        return -1;
    for file_stat in files_list:
        if os.path.isfile(file_stat['name']):
            fd = open(file_stat['name'],'w')
            fd.close()
            print "clear file" + file_stat['name']
    log("Clear %s complete" % fulllogpath)

def conf_cmp(confs1,confs2):
    if confs1['opt'] == 'delete':
        if confs2['opt'] == 'delete':
            return 0;
        else:
            return -1
    elif confs2['opt'] == 'delete':
        return 1;
    else:
        return 0

def free_space():
    global conf_list
    conf_list.sort(cmp=conf_cmp)
    for confs in conf_list:
        if confs['opt'] == 'delete':
            if limit_size == 6:
                delete_file(confs)
            elif limit_size >= 7:
                delete_file(confs)
                delete_file_by_range(confs)#param3
        elif confs['opt'] == 'clear':
            clear_file(confs)
        elif confs['opt'] == 'gzip':
            gzip_file(confs)
        else:
            log(str(confs)+': operat errro')

def free_delete_log():
    proc_list = glob.glob('/proc/[1-9][0-9][0-9]*/fd/*')
    for proc_file in proc_list:
        try:
            ori_file = proc_file.strip()
            if ori_file == "":
                print "ori_file %s is empty" %s
                continue
            if os.path.islink(proc_file):
                ori_file = os.readlink(proc_file)
            if not os.path.isfile(proc_file):
                continue
            if ori_file.find(' (deleted') != -1 and (ori_file.find('log') != -1 or ori_file.find('magick') != -1):
                #fd_proc = open(proc_file,'w')
                #fd_proc.close()
                print 'clear fd file %s' % proc_file
                write_cleared_log(ori_file,'clear',ori_file)

        except Exception,e:
            print str(e)
            log('clear pid file failed, %s' % str(e))

def check_pid():
    global pid_file_name
    if os.path.isfile(pid_file_name):
        fd_pid = open(pid_file_name,'r')
        lastpid = fd_pid.read().strip()
        fd_pid.close()
        proc_pid = os.path.join('/proc/',lastpid)

        print "check_pid proc_pid: %s" % proc_pid
        print "check_pid last_pid: %s" % lastpid

        if lastpid != '' and os.path.isdir(proc_pid) and os.listdir(proc_pid):
            last_unix_time = os.path.getctime(proc_pid)
            now_unix_time = time.time()
            if (now_unix_time - last_unix_time) >= 3600:
                os.killpg(int(lastpid),signal.SIGKILL)
                log("last clear process does not exit,maybe exception happens(force quit)")
            else:
                return False
    fd_pid = open(pid_file_name,'w')
    fd_pid.write(str(os.getpid()))
    fd_pid.close()
    return True
            
def do_close():
    global fd_log,fd_cleared_log
    fd_log.close()
    fd_cleared_log.close()
    
def doexport():
    global export_rules
    for rule in export_rules:
        try:
            key = rule.split("=")[0]
            cmd = """if [[ -z `grep '%s' /etc/profile` ]];then echo "export %s" >> /etc/profile; elif [[ -z `grep '%s' /etc/profile` ]];then sed -i 's/^export %s.*/export %s/g' /etc/profile;else exit;fi;source /etc/profile""" % (key,rule,rule,key,rule)
            s = subprocess.Popen(args=cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            ret = s.stdout.read() 
            print ret
            log(rule)
        except Exception,e:
            log("export failed, %s" % str(e))
            print e

def delete_itil_oldfile():
  itil_mmin = 30*24*60
  itil_del_list = []
  for dir in ['/home/charlie/itil/peer/bt/','/home/charlie/itil/peer/chgbackup/','/home/charlie/itil/peer/job/']:
    for filename in glob.glob(os.path.join(dir,'*')):
      if os.path.isdir(filename):
        dirname = filename
        try:
          (imode, iino, idev, inlink, iuid, igid, isize, iatime, imtime, ictime) = os.stat(dirname)
          nowtime = time.time()
          if (nowtime - imtime)/60 <= itil_mmin:
            continue
          if not os.listdir(dirname):
            os.rmdir(dirname)
            print "remove dir " + dirname
            write_cleared_log(dirname,'delete',0)
            continue
          itil_del_list.extend(find_file(root=dirname,isrecursion=True,filepattern='*',mmin=itil_mmin))
        except Exception,e:
          print str(e)
      else:
        log("delete_itil_oldfile() error file %s"%filename)
  if len(itil_del_list) == 0:
    log("delete_itil_oldfile() no files to delete")
    return 0
  log("delete_itil_oldfile() will delete %d files" % len(itil_del_list))
  for file_stat in itil_del_list:
    try:
      name = file_stat['name']
      if os.path.isfile(name):
        os.remove(name)
        print "remove file "+name
      elif os.path.isdir(name) and not os.listdir(name):
        os.rmdir(name)
        print "remove dir "+name
      elif os.path.islink(name) and not os.path.exists(os.readlink(name)):
        os.remove(name)
        print "remove broken link file "+name
      else:
        continue
      write_cleared_log(name,'delete',file_stat['uid'])
    except Exception,e:
      print str(e)
      log("Delete %s failed : %s" % (fulllogpath,str(e)))
  log("delete_itil_oldfile() delete complete")
  return 0

def main():
    global pid_file_name,thenices
    pid_status = check_pid()
    if not pid_status:
        return -1
   
    #thenices = os.nice(19-thenices)

    check_disk()
    log("clear disk start:")
    load_status = load_config()
    if load_status != 0:
        return -1
    free_space()
    
    fd_pid = open(pid_file_name,'w')
    fd_pid.close()
    print "clear pid file "+pid_file_name

    files_list = find_file(root='/home/charlie/log/',isrecursion=False,filepattern='clear_*.log',mmin=180*24*60)
    files_list.extend(find_file(root='/home/charlie/log/',isrecursion=False,filepattern='beencleared_*.log',mmin=180*24*60))
    for confs in files_list:
        os.remove(confs['name'])
        print "remove qslog file "+confs['name']
   
    #delete by francowu
    #free_delete_log()
    doexport()
    #add by francowu
    delete_itil_oldfile()
    do_close()
    return 0

if __name__ == "__main__":
    main()
