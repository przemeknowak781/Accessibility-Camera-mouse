@echo off
setlocal
cd /d %~dp0
start "" /min cmd /c "python main.py"
endlocal
