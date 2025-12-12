@echo off
set IP=170.64.186.179
set USER=root
set PWD=IfconfigminusA@1s

echo ===================================================
echo DEPLOYING ASYNCRAT SERVER TO %IP%
echo ===================================================

echo [1/3] Uploading Server Files...
echo (You may be asked for the password: %PWD%)
scp -r Server %USER%@%IP%:/root/asyncrat_server

echo [2/3] Setting Permissions...
ssh %USER%@%IP% "chmod +x /root/asyncrat_server/setup.sh"

echo [3/3] Running Setup Script on VPS...
ssh %USER%@%IP% "cd /root/asyncrat_server && ./setup.sh"

echo.
echo ===================================================
echo DEPLOYMENT COMPLETE!
echo Try accessing: http://%IP%:5000
echo ===================================================
pause
