@echo off
setlocal

cd /d "%~dp0"

if not exist "logging_execution\system\scheduler" mkdir "logging_execution\system\scheduler"

echo.>> "logging_execution\system\scheduler\rivex_cron.log"
echo ================================================>> "logging_execution\system\scheduler\rivex_cron.log"
echo [%date% %time%] Iniciando o Rivex...>> "logging_execution\system\scheduler\rivex_cron.log"

".venv\Scripts\python.exe" "main.py" --pipeline all >> "logging_execution\system\scheduler\rivex_cron.log" 2>&1

set "EXIT_CODE=%ERRORLEVEL%"

echo [%date% %time%] Execucao finalizada. Codigo: %EXIT_CODE%>> "logging_execution\system\scheduler\rivex_cron.log"

exit /b %EXIT_CODE%
