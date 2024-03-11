python3.8 -V || apt install python3.8
go version || apt install golang

echo "Package installing..."
echo -n "HTTProuter " & go get github.com/julienschmidt/httprouter && echo "success!" || echo "FAIL!"
echo -n "Pudge " & go get github.com/recoilme/pudge && echo "success!" || echo "FAIL!"
echo -n "Colorizer " & go get github.com/Elchinchel/colorizer && echo "success!" || echo "FAIL!"
echo -n "Mutagen " & python3.8 -m pip install mutagen && echo "success!" || echo "FAIL!"
echo -n "Telethon " & python3.8 -m pip install telethon && echo "success!" || echo "FAIL!"
echo -n "Requests " & python3.8 -m pip install requests && echo "success!" || echo "FAIL!"
echo -n "AIOhttp " & python3.8 -m pip install aiohttp && echo "success!" || echo "FAIL!"

chmod +x compile.sh

echo "Compiling binaries..."
./compile.sh

chmod +x start.sh
echo "Done!"