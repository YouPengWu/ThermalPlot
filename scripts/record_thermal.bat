@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

:: === Configuration ===
set IPMI_HOST=
set IPMI_USER=
set IPMI_PASS=

:: === Custom IPMI Raw Command Settings ===
:: User can define NetFn, Cmd, and Data here
set IPMI_RAW_NETFN=
set IPMI_RAW_CMD=
set IPMI_RAW_DATA=

:: === Ask for Duration ===
set /p DURATION_SEC="Enter duration to run (in seconds): "

:: Validate input (basic check)
set "var="&for /f "delims=0123456789" %%i in ("%DURATION_SEC%") do set var=%%i
if defined var (
    echo Error: Duration must be a number.
    pause
    exit /b
)

:: === Generate Log Filename with Timestamp ===
:: Get date/time in independent format if possible, but standard %date% %time% depends on locale.
:: Using a simple name is safer, but let's try to make it unique.
set LOGFILE=thermal_log_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.txt
:: Clean up filename (replace spaces with 0 if single digit hour)
set LOGFILE=%LOGFILE: =0%

echo Starting recording for %DURATION_SEC% seconds... > %LOGFILE%
echo Log saved to: %LOGFILE%

:: === Initialize Timer ===
:: Get start time in seconds (0-86399)
call :get_time_seconds start_s

set /a end_s=!start_s! + %DURATION_SEC%
set /a count=0

:loop
set /a count+=1

:: Get current time
call :get_time_seconds now_s

:: Handle midnight crossing (if now < start, add 24h)
if !now_s! lss !start_s! set /a now_s+=86400

set /a elapsed=!now_s! - !start_s!

:: Check duration
if !elapsed! geq %DURATION_SEC% (
    echo [Info] Time limit %DURATION_SEC%s reached. >> %LOGFILE%
    echo [Info] Time limit %DURATION_SEC%s reached.
    goto end
)

echo.
echo Run number !count!
echo [Elapsed time: !elapsed! seconds]

:: Write header to log
echo. >> %LOGFILE%
echo Run number !count! >> %LOGFILE%
echo echo [Elapsed time: !elapsed! seconds] >> %LOGFILE%

:: Run IPMI Commands
ipmitool -I lanplus -H %IPMI_HOST% -U %IPMI_USER% -P %IPMI_PASS% sdr type Temperature >> %LOGFILE%
ipmitool -I lanplus -H %IPMI_HOST% -U %IPMI_USER% -P %IPMI_PASS% raw %IPMI_RAW_NETFN% %IPMI_RAW_CMD% %IPMI_RAW_DATA% >> %LOGFILE%

:: Simple delay (1 second)
timeout /t 1 /nobreak >nul

goto loop

:end
echo Execution Completed.
pause
exit /b

:: === Helper Function: Get Time in Seconds ===
:get_time_seconds
for /f "tokens=1-3 delims=:.," %%a in ("%time%") do (
    set /a h=1%%a-100
    set /a m=1%%b-100
    set /a s=1%%c-100
    set /a %1=!h!*3600+!m!*60+!s!
)
exit /b
