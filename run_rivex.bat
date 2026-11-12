
@echo off
setlocal

cd /d "C:\Users\victor.amador\Documents\projects\Rivex"

if not exist "logs" mkdir "logs"

echo.>> "logs\rivex_cron.log"
echo ================================================>> "logs\rivex_cron.log"
echo [%date% %time%] Iniciando o Rivex...>> "logs\rivex_cron.log"

".venv\Scripts\python.exe" "main.py" --pipeline all >> "logs\rivex_cron.log" 2>&1

set "EXIT_CODE=%ERRORLEVEL%"

echo [%date% %time%] Execucao finalizada. Codigo: %EXIT_CODE%>> "logs\rivex_cron.log"

exit /b %EXIT_CODE%
