#!/usr/bin/python
#author: aragonzhang
#last update: 2011-07-28
import pexpect,urllib2,os,sys,time,re,threading
lock=threading.Lock()
tlock=threading.Lock()
threads={}
pre2ip={}; host2ip={}; module2ip={}; net2ip={}; idc2ip={}; status2ip={}; sysver2ip={}; devtype2ip={}; rsp2ip={}; f12ip={}; f22ip={}; f32ip={}; ip2ip={}; conv={} ;product2ip={};city2ip={};ip2name={}

if "NEW_ANT" in sys.argv[0]:
  version = 1
else:
  version = 0

def usage():
  if version == 0:
    print 'Usage:',sys.argv[0],' <cmd> <ip|host|group|exp> [user] [threadCount]'
  else:
    print 'Usage:',sys.argv[0],' <src> <ip|host|group|exp> <dest> [user] [threadCount]'

def ssh(host='127.0.0.1',user='charlie',cmd='uptime'):
  account=os.popen('whoami').read().strip()
  os.popen('echo "W %s %s %s %s" |/home/charlie/bin/udp_client.py 127.0.0.1 9999'%(account,host,user,cmd.replace('"','\\"'))).read()
  url=file('/home/charlie/etc/passurl.conf').read()%(user,host)
  password=urllib2.urlopen(url).read()
  child=pexpect.spawn('/usr/local/bin/ssh -q -p 36000 -l %s %s %s'%(user, host, cmd), timeout=30,maxread=9999999)
  child.setecho(False)
  exp_list=[pexpect.TIMEOUT, pexpect.EOF, "assword:", "yes/no", "Interrupted system call"]
  ret=child.expect(exp_list)
  fail_count=0
  while ret!=0 and ret!=1:
    if ret==2:
      child.sendline(password)
      fail_count+=1
      if fail_count==3:
        return "%s %s password error"%(host,user)
    elif ret==3:
      child.sendline('yes')
    elif ret==4:
      child.sendline('')
    ret=child.expect(exp_list)
  return child.before.strip()

def scp(host='127.0.0.1',user='charlie',src='/tmp/test.conf',dest='/tmp/test.conf'):
  url=file('/home/charlie/etc/passurl.conf').read()%(user,host)
  password=urllib2.urlopen(url).read()
  cmd='/usr/local/bin/scp -q -P 36000 %s "%s@%s:%s"'%(src, user, host, dest)
  #print cmd
  child=pexpect.spawn(cmd, timeout=30,maxread=9999999)
  child.setecho(False)
  exp_list=[pexpect.TIMEOUT, pexpect.EOF, "'s password:", "yes/no", "Interrupted system call"]
  ret=child.expect(exp_list)
  fail_count=0
  while ret!=0 and ret!=1:
    if ret==2:
      child.sendline(password)
      fail_count+=1
      if fail_count==3:
        return "%s %s password error"%(host,user)
    elif ret==3:
      child.sendline('yes')
    elif ret==4:
      child.sendline('')
    ret=child.expect(exp_list)
  return child.before.strip()

def add(dictionary,k,v):
  if not k in dictionary:
    dictionary[k]=[v]
  else:
    dictionary[k].append(v)

def get_ip(exp,f):
  global pre2ip,host2ip,module2ip,net2ip,idc2ip,status2ip,sysver2ip,devtype2ip,rsp2ip,f12ip,f22ip,f32ip,ip2ip,product2ip,city2ip
  if f==0:
    alldict=[pre2ip,host2ip,module2ip,net2ip,idc2ip,devtype2ip,rsp2ip,ip2ip,status2ip,sysver2ip]
  else:
    alldict=[pre2ip,host2ip,module2ip,net2ip,idc2ip,devtype2ip,rsp2ip,f12ip,f22ip,f32ip,ip2ip,status2ip,sysver2ip,product2ip,city2ip]
  ret={}
  exp=exp.replace('-','').replace('+','').replace(' ','')
  if exp.lower()=='all':
    return ip2ip.keys()
  if re.match('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',exp):
    return [exp]
  c=0
  for i in alldict:
    if exp in i:
      for j in i[exp]:
        ret[j]=''
    c+=1
  return ret.keys()

def list_and(a,b):
  ret=[]
  for i in a:
    if i in b:
      ret.append(i)
  return ret

def list_not(a,b):
  ret=[]
  for i in a:
    if i not in b:
      ret.append(i)
  return ret

def parse_exp(exp):
  global conv
  rp='(\-{0,1}\+{0,1} {0,1}[a-zA-z0-9`]{1,50})'
  rp='(\-{0,1}\+{0,1} {0,1}[a-zA-z]{1,50}[0-9`]{0,50}[a-zA-z]{1,50}[0-9`]{0,50})'
  allip=[]
  for i in exp.strip(' ').split(' '):
    allip1=[]
    for j in conv:
      if j in i:
        i=i.replace(j,conv[j])
    try:
      int(i[0])
      allip1+=get_ip(i,0)
    except:pass
    ret=re.findall(rp,i)
    if ret:
      allip1+=get_ip(ret[0],0)
      for j in ret[1:]:
        tmpret=get_ip(j,1)
        if j[0]=='+':
          allip1=list_and(allip1,tmpret)
        elif j[0]=='-':
          allip1=list_not(allip1,tmpret)
        else:
          allip1+=tmpret
    allip+=allip1
  return {}.fromkeys(allip).keys()

def worker(ip,user,cmd,src,dest):
  global lock,tlock,threads,version,ip2name
  ret=''
  if version == 0:
    try:
      ret+='%s'%ssh(ip,user,cmd)
    except:
      pass
  else:
    try:
      ret+='%s'%scp(ip,user,src,dest).replace('\nReceived signal 1. (no core)','')
    except:
      pass
  lock.acquire()
  try:
    print ip2name[ip]
  except:
    pass
  try:
    print ret.strip('\n')
  except Exception,e:
    pass
  lock.release()
  tlock.acquire()
  if ip in threads:
    threads.pop(ip)
  tlock.release()

def main():
  global pre2ip,host2ip,module2ip,net2ip,idc2ip,status2ip,sysver2ip,devtype2ip,rsp2ip,f12ip,f22ip,f32ip,ip2ip,threads,tlock,lock,conv,product2ip,version,city2ip,ip2name
  qqlst='/home/charlie/etc/qq.lst'
  tc=1
  src=''
  dest=''
  cmd=''
  if version == 0:
    if len(sys.argv)<3 or (len(sys.argv)==5 and sys.argv[4].isdigit()==False):
      usage()
      return
    elif  len(sys.argv)==4 and sys.argv[3].isdigit()==True:
      cmd,exp,tc=sys.argv[1:4]
      user='charlie'
    elif len(sys.argv)==3:
      cmd,exp=sys.argv[1:3]
      user='charlie'
    elif len(sys.argv)==4:
      cmd,exp,user=sys.argv[1:4]
    else:
      cmd,exp,user,tc=sys.argv[1:5]
  else:
    if len(sys.argv)<4 or (len(sys.argv)==6 and sys.argv[5].isdigit()==False):
      usage()
      return
    elif  len(sys.argv)==5 and sys.argv[4].isdigit()==True:
      src,exp,dest,tc=sys.argv[1:5]
      user='charlie'
    elif len(sys.argv)==4:
      src,exp,dest=sys.argv[1:4]
      user='charlie'
      #print 'here',src,exp,dest,user
    elif len(sys.argv)==5:
      src,exp,dest,user=sys.argv[1:5]
    else:
      src,exp,dest,user,tc=sys.argv[1:6]
  #print sys.argv,'\n',version,exp,cmd,src,dest,user,tc
  tc=int(tc)
  if tc>100:
    tc=100
  cmd=cmd.replace('"','\\"').replace("'","\\'")
  rows=file(qqlst).read().strip('\n').split('\n')
  for i in rows[1:]:
    try:
      name,net,idc,status,sysver,ipout,module,devtype,rsp,f1,f2,f3,f4,product,city=i.split('\t')[:15]
    except Exception,e:
      print 'qq.lst error',i,e
    try:
      name,ip=name.replace('"','').split('=')
    except:
      continue
    if '-' in f1:
      conv[f1]=f1.replace('-','`')
      f1=f1.replace('-','`')
    if '-' in f2:
      conv[f2]=f2.replace('-','`')
      f2=f2.replace('-','`')
    if '-' in f3:
      conv[f3]=f3.replace('-','`')
      f3=f3.replace('-','`')
    add(pre2ip,re.sub('\d*$','',name.replace('_','')),ip)
    add(host2ip,name,ip)
    add(module2ip,module,ip)
    add(net2ip,net.replace('#',''),ip)
    add(idc2ip,idc,ip)
    add(status2ip,status,ip)
    add(sysver2ip,sysver,ip)
    add(devtype2ip,devtype.split(' ')[0],ip)
    add(rsp2ip,rsp,ip)
    add(f12ip,f1,ip)
    add(f22ip,f2,ip)
    add(f32ip,f3,ip)
    add(ip2ip,ip,ip)
    add(product2ip,product,ip)
    add(city2ip,city,ip)
    ip2name[ip]=name
  all=parse_exp(exp) 
  #print all;return
  for i in all:
    t=threading.Thread(target=worker,args=[i,user,cmd,src,dest])
    t.setDaemon( True )
    t.start()
    tlock.acquire()
    threads[i]=''
    tlock.release()
    while threading.activeCount()>tc:
      time.sleep(0.1)
  if len(threads)>1:
    time.sleep(1)
  while len(threads)>0:
    time.sleep(5)
    lock.acquire()
    sys.stderr.write("%s\n"%' '.join(threads.keys()))
    lock.release()

if __name__=='__main__':
  #print scp()
  main()
  #try:main()
  #except:pass
