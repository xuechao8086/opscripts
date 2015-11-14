#!/usr/bin/env python2.7
#coding:utf8

"""
Author:         charliezhao
Filename:       mysql.py
Create Time:    2015-09-12 11:21
Description:
                
"""
import MySQLdb
import time

def insert_test_innodb_lock(cursor):
    sql = "set autocommit=False;"
    cursor.execute(sql)
    for i in xrange(2**10):
        sql = "insert into test_innodb_lock(`a`, `b`) values({}, 'b{}')"\
                .format(i, i)
        cursor.execute(sql)
        
    sql = "commit;"
    cursor.execute(sql)

if __name__ == '__main__':
    conn = MySQLdb.connect(host="localhost",user="root",passwd="tingting2024",db="job",charset="utf8")  
    cursor = conn.cursor()
    
    insert_test_innodb_lock(cursor)

    #time.sleep(3600)     
