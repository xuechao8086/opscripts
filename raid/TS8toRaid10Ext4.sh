#!/bin/sh
#author: charliezhao
source /etc/profile
kvstat="`ps -ef |grep -v grep|grep -v CK|grep -c kvsvr`"
kernel=$(cat /etc/issue |grep -ic release)
if [[ $kvstat -ne 0 ]]
then
    echo "kv is running,check it"
    exit 1
fi

if [ -d /home/charlie/bin ]
then
    /home/charlie/bin/ossattragentConsole pause;
    /home/charlie/bin/mmdataagentConsole pause;
fi

if [ "(df -h|grep md0)" != '' ]
then
    umount /dev/md0
fi

if [ "(df -h|grep md127)" != '' ]
then
    umount /dev/md127
fi

if [ -b /dev/md0 ]
then
    /sbin/mdadm -S --force /dev/md0
fi

if [ -b /dev/md127 ]
then
    /sbin/mdadm -S --force /dev/md127
fi

disk_arr=(/dev/sdb /dev/sdc /dev/sdd /dev/sde /dev/sdf /dev/sdg /dev/sdh /dev/sdi /dev/sdj /dev/sdk /dev/sdl)
for disk in ${disk_arr[@]}
do
    if [ ! -b ${disk} ]
    then
        echo "error ${disk} not exists"
        exit
    fi
done

disk_arr1=(/dev/sdb1 /dev/sdc1 /dev/sdd1 /dev/sde1 /dev/sdf1 /dev/sdg1 /dev/sdh1 /dev/sdi1 /dev/sdj1 /dev/sdk1 /dev/sdl1)

for disk in ${disk_arr1[@]}
do
    if [ "$(df -h|grep ${disk})" != '' ]
    then
        umount ${disk}
        if [ $? -ne 0 ]
        then
            echo "error umount ${disk} fail"
            exit
        fi
    else
        echo "info umount ${disk} ok"
    fi
done

now=$(date +"%Y-%m-%d %H:%M:%S")
echo "${now} fdisk begin"
for device in ${disk_arr[@]}
do 
        /sbin/fdisk $device 2>&1 << EOF
d
n
p
1
1
36481
t
fd
p
w
EOF
done
now=$(date +"%Y-%m-%d %H:%M:%S")
echo "${now} fdisk done"
if [ -b /dev/md0 ]
then
    /sbin/mdadm -S --force /dev/md0
fi
if [ -b /dev/md127 ]
then
    /sbin/mdadm -S --force /dev/md127
fi    
yes | /sbin/mdadm --create /dev/md0 --level=10 --force  --raid-devices=10   /dev/sdb1 /dev/sdc1 /dev/sdd1 /dev/sde1 /dev/sdf1 /dev/sdg1 /dev/sdh1 /dev/sdi1 /dev/sdj1 /dev/sdk1

if [ $? -ne 0 ]
then
    echo "/sbin/mdadm --create /dev/md0 --level=10  --raid-devices=10   /dev/sdb1 /dev/sdc1 /dev/sdd1 /dev/sde1 /dev/sdf1 /dev/sdg1 /dev/sdh1 /dev/sdi1 /dev/sdj1 /dev/sdk1 fail"
else
    echo "/sbin/mdadm --create /dev/md0 --level=10  --raid-devices=10   /dev/sdb1 /dev/sdc1 /dev/sdd1 /dev/sde1 /dev/sdf1 /dev/sdg1 /dev/sdh1 /dev/sdi1 /dev/sdj1 /dev/sdk1 ok"
fi

/sbin/mdadm --manage /dev/md0 --add /dev/sdl1

if [ $? -ne -0 ]
then
    echo '/sbin/mdadm --manage /dev/md0 --add /dev/sdl1 fail'
fi

now=$(date +"%Y-%m-%d %H:%M:%S")
echo "${now} /sbin/mkfs.ext4 /dev/md0 begin"

/sbin/mkfs.ext4 /dev/md0

if [ $? -eq 0 ]
then
    echo "ts8 to raid10 ok"
else
    echo "ts8 to raid10 fail"
fi

echo "${now} /sbin/mkfs.ext4 /dev/md0 done"

if [ ! -f /etc/mdadm.conf ]
then
        touch /etc/mdadm.conf
fi

info=`/sbin/mdadm --detail --scan`

/sbin/mdadm -Es > /etc/mdadm.conf


if [[ $(grep "/sbin/mdadm -As /dev/md0" /etc/rc.d/boot.local) == "" ]]
then
        echo "/sbin/mdadm -As /dev/md0" >> /etc/rc.d/boot.local 
fi

for var in {b..l}
do 
    sed -i "/\/dev\/sd${var}1/d" /etc/fstab
done


sed -i "/data1/d" /etc/fstab
sed -i "/data4/d" /etc/fstab

echo "/dev/md0            /data1               ext4       noatime,acl,user_xattr  1  2" >>  /etc/fstab

if [[ $(ls / | grep data1) == "" ]]
then
    mkdir /data1
fi

/bin/mount -a

if [ -d /home/charlie/bin ]
then
    unlink /home/charlie/data
    mkdir -p /data1/charlie/data
    ln -s /data1/charlie/data /home/charlie/data
    chown -R charlie.users /home/charlie/data
    chown -R charlie.users /data1/charlie
    /home/charlie/bin/ossattragentConsole start >/dev/null 2>&1;
    /home/charlie/bin/mmdataagentConsole start > /dev/null 2>&1;

fi



#=====raid check
if [ -f /usr/sbin/raid-check ]
then 
    mv /usr/sbin/raid-check /usr/sbin/raid-check.bak
    if [ $? -ne 0 ]
    then
        echo "error mv /usr/sbin/raid-check /usr/sbin/raid-check.bak fail"
    fi
fi

#=====io scheduler deadline
if [[ $kernel -eq 0 ]]
then
        sed -i "/^echo deadline/d" /etc/init.d/boot.local
        echo deadline > /sys/block/md0/queue/scheduler
        echo "echo deadline > /sys/block/md0/queue/scheduler" >> /etc/init.d/boot.local
else
        sed -i "/^echo deadline/d" /etc/rc.local
        echo deadline > /sys/block/md0/queue/scheduler
        echo "echo deadline > /sys/block/md0/queue/scheduler" >> /etc/rc.local

fi


echo 4096 >/sys/block/md0/md/stripe_cache_size
[ ! -n "`grep stripe_cache_size /etc/rc.d/boot.local`" ] && echo "echo 4096 >/sys/block/md0/md/stripe_cache_size" >> /etc/rc.d/boot.local
