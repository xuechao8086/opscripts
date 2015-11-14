#!/bin/sh
cd /home/charlie/bin/raid_tools/
./MegaCli64 -LdPdInfo  -aALL 
./MegaCli64  -LDInfo -Lall -aALL
./MegaCli64   -CfgLdDel -L1 -Force -a0; ./MegaCli64 	-CfgLdDel -L2 -Force -a0; ./MegaCli64 -CfgLdAdd -r5 [12:2,12:3,12:4,12:5,12:6,12:7,12:8,12:9,12:10,12:11]  -a0



#/usr/bin/rsync -av 172.27.18.33::nhadoop/e2fsprogs-1.42.7.ts6.tar.gz /home/charlie/upload/
#cd /home/charlie/upload
#tar zxvf e2fsprogs-1.42.7.ts6.tar.gz
#cd /home/charlie/upload/e2fsprogs-1.42.7
#./configure; make -j; make install;
/sbin/mke2fs -O 64bit,has_journal,extents,huge_file,flex_bg,uninit_bg,dir_nlink,extra_isize /dev/md0


#fdisk /dev/sdb
mkfs.ext4 /dev/sdb1
