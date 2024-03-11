#!/bin/bash
DBport=56101
LPport=56001

trap 'kill 0' EXIT

./longpoll/lp $LPport &

cat | python3.8 RBClub.py -db $DBport -lp $LPport &

./database/db $DBport