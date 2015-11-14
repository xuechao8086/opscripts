#!/usr/bin/python
#-*- encoding:utf-8 -*-

import os,glob,sys,time
import logging,commands,datetime

nkeep_days = 10;
HADOOP_CMD = "/usr/local/hadoop/bin/hadoop";
HIVELOG_SRC_HPATH = " /data/charlie/log/hivelog";
HIVELOG_DST_HPATH = "/data_need2del/hivelog/";

def gen_del_list():
    szSrcPath = HIVELOG_SRC_HPATH + "/" + "\*/";

    stDelList = []
    szDelFiles = ""
    check_date = (datetime.date.today() - datetime.timedelta(days=nkeep_days));
    szCMD = "%s fs -ls %s | grep -v ^Found | awk '{print $NF}'" % (HADOOP_CMD, szSrcPath);

    fp = os.popen(szCMD, "r");
    for line in fp:
        if line.strip() == "" :
            continue;
        hfile = line.strip().split('/')[-1];
        username = line.strip().split('/')[-2];

        date_str = hfile.split('_')[1];
        file_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date();
        ##sys.stderr.write("hfile[%s] date[%s]\n" % (hfile, date_str));
        if file_date < check_date:
            szDelFiles += "%s/%s/%s " % (HIVELOG_SRC_HPATH, username, hfile);
        if len(szDelFiles) > 10240:
            stDelList.append(szDelFiles);
            szDelFiles = ""

    fp.close();
    if len(szDelFiles) > 0 :
        stDelList.append(szDelFiles);

    return stDelList;

def clean_history_hivelog():
    iRet, stDelList = 0, gen_del_list();
    for szDelFiles in stDelList:
        ##sys.stderr.write("%s\n" % (szDelList));
        if szDelFiles.strip() != "" :
            szDelCMD = "%s fs -rm -r -skipTrash %s" % (HADOOP_CMD, szDelFiles);
            iRet = os.system(szDelCMD);
            sys.stderr.write("iRet[%d] of CMD[%s]\n" % (iRet, szDelCMD));

if __name__ == "__main__":

    clean_history_hivelog();
    sys.exit(0);


