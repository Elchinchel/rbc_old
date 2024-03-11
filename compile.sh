cd longpoll
go build lp.go && echo "LP binary compiled"
chmod +x lp
cd ../

cd database
go build db.go && echo "DB binary compiled"
chmod +x db
cd ../