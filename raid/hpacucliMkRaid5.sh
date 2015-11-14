#!/bin/sh
cd /home/charlie/bin/raid_tools
./hpacucli controller all show config     
./hpacucli  controller slot=3 array B delete forced     
./hpacucli  controller slot=3 array C delete forced   
./hpacucli ctrl slot=3 create type=ld drives=allunassigned raid=5

