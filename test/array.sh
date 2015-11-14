#!/bin/sh
#man bash, to see more about arr
declare -a arr

for((i=0;i<10;i++))
do
    arr[$i]=$i
    echo ${arr[$i]}
done

str=''
for i in $(seq 1 10)
do
    str="$str $i"
    echo $str
done

arr1=(${str})
echo "arr1: ${arr1[3]}"
arr1[4]="xuechao"
echo "arr1[4]:${arr1[4]}"

arr1['charlie']='zhao'
echo '--'



for i in ${arr1[@]}
do
    echo $i
done
echo 'another test'
i=0
while [ $i -lt ${#arr1[@]} ]
do
    echo "${i} ${arr[$i]}"
    let ++i
done
arr1['charlie']='zhao'
echo ${arr["charlie"]}


