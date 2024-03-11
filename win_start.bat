set DBport=56101
set LPport=56001

start ./longpoll/lp %LPport%

start "ping 127.0.0.1 -n 5 > nul; py RBClub.py -db %DBport% -lp %LPport%"

"./database/db" %DBport%

taskkill /f /im "lp.exe"