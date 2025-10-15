@echo off
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Starting Mining Management Server...
python app.py

pause