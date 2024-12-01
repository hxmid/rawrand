@echo off
copy /y ..\settings.json .
git fetch
git pull
python -m pip install -r requirements.txt
