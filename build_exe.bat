@echo off
cd /d C:\Users\ADMIN\Desktop\remer
echo ==============================================
echo Building Standalone CalendarAssistant App...
echo ==============================================

echo.
echo 1. Ensuring PyInstaller package is installed...
py -3.12 -m pip install pyinstaller

echo.
echo 2. Running PyInstaller compilation...
:: --onefile packages everything to a single executable
:: --noconsole hides the default cmd terminal so it runs like a native app
:: --name sets the output binary name
py -3.12 -m PyInstaller --onefile --noconsole --name="CalendarAssistant" sticky_notes.py

echo.
echo ==============================================
echo Compilation finished!
echo Your executable is ready at:
echo C:\Users\ADMIN\Desktop\remer\dist\CalendarAssistant.exe
echo ==============================================
echo Done!
