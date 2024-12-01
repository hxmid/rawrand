winget install --id=Chromium.ChromeDriver -e --accept-package-agreements --accept-source-agreements
copy /y ..\settings.json .
git fetch
git pull
python -m pip install -r requirements.txt
echo "done :)"
