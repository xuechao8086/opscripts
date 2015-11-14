#!/bin/sh
#author: charliezhao

#/usr/bin/rsync -av 172.27.18.33::nhadoop/e2fsprogs-1.42.7.ts6.tar.gz /home/charlie/upload/
#cd /home/charlie/upload
#tar zxvf e2fsprogs-1.42.7.ts6.tar.gz
#cd /home/charlie/upload/e2fsprogs-1.42.7
#./configure; make -j; make install;
if [ "$(df -h | grep md0)" != '' ]
then
    umount /dev/md0
    if [ $? -ne 0 ]
    then
        echo "/dev/md0 busy, check it!"
        exit 1
    fi
fi

mdadm -S /dev/md0
for i in {b..m}
do
    if [ ! -b  /dev/sd${i} ]
    then
        echo "error: /dev/sd${i} not exists,check it!"
        exit 1
    fi	
    if [ "$(df -h | grep sd${i}1)" != '' ]
    then
        umount /dev/sd${i}1
        if [ $? -ne 0 ]
        then
            echo "/dev/sd${i}1 busy, check it!"
            exit 1
        fi
    fi
done

for i in {b..m}
do
	/sbin/fdisk /dev/sd${i} 2>&1 <<  EOF
d
n
p
1
1
243201
t
fd
w
EOF
done
echo  create  raid5...... 
yes | /sbin/mdadm --create /dev/md0 --level=5  --raid-devices=12  /dev/sdb1 /dev/sdc1 /dev/sdd1 /dev/sde1 /dev/sdf1 /dev/sdg1 /dev/sdh1 /dev/sdi1 /dev/sdj1 /dev/sdk1 /dev/sdl1 /dev/sdm1

echo Formating FileSystem......  
#/sbin/mke2fs -O 64bit,has_journal,extents,huge_file,flex_bg,uninit_bg,dir_nlink,extra_isize -i 4194304 /dev/md0
/sbin/mke2fs -O 64bit,has_journal,extents,huge_file,flex_bg,uninit_bg,dir_nlink,extra_isize /dev/md0
#/sbin/mkfs.ext3 /dev/md0

if [ ! -f /etc/mdadm.conf ]
then
        touch /etc/mdadm.conf
fi


echo Updating /etc/mdadm.conf......
/sbin/mdadm -Es > /etc/mdadm.conf


if [[ $(grep "/sbin/mdadm -As /dev/md0" /etc/init.d/boot.local) == "" ]]
then
        echo /sbin/mdadm -As /dev/md0 >> /etc/init.d/boot.local
fi

for  i in {b..m}
do
	sed -i "/\/dev\/sd${i}1/d" /etc/fstab
done

sed -i "/md0/d" /etc/fstab

if [[ $(grep "/dev/md0            /data1               ext4       noatime,acl,user_xattr  1  2" /etc/fstab) == "" ]]
then
       echo "/dev/md0            /data1               ext4       noatime,acl,user_xattr  1  2" >>  /etc/fstab
fi

if [[ $(ls / | grep data1) == "" ]]
then
    mkdir /data1
fi

/bin/mount -a


echo  update  the  mysql......

myip=`ip -f inet addr | grep global | awk '{print $2}' | awk -F/  '{print $1}'`

mysql -ucharlie -pforconnect -h172.27.19.230  -e "use db_devconfig;select svrid  from svr_ip_info where ip = \"$myip\";"  >  mysvrid

svid=`tail -1 mysvrid` 

mysql -ucharlie -pforconnect -h172.27.19.230  -e "use db_devconfig;update server_info set devtype = 'TS6 Raid5' where svrid = \"$svid\" and devtype = 'TS8 No Raid';"

