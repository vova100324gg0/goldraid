@echo off
rem ------------------------------------------------------------------
rem  Philips 40PUT6400/60 (QM152E, Android 5.1.1) - ADB helper
rem  Usage:  tv-adb.cmd connect | status | clean | install <file.apk>
rem          tv-adb.cmd shell "<command>"
rem
rem  Адрес телевизора задаётся одним из способов:
rem    1) переменная окружения:  set TV=192.168.1.50:5555
rem    2) файл tv-ip.txt рядом со скриптом (одна строка — адрес)
rem    3) значение по умолчанию ниже (замените на адрес своего ТВ)
rem ------------------------------------------------------------------
setlocal
set "ADB=%LOCALAPPDATA%\platform-tools\adb.exe"
if not defined TV if exist "%~dp0tv-ip.txt" for /f "usebackq tokens=* delims=" %%i in ("%~dp0tv-ip.txt") do set "TV=%%i"
if not defined TV set "TV=192.168.1.100:5555"

if not exist "%ADB%" (
  echo [X] adb not found at %ADB%
  exit /b 1
)

if /i "%~1"=="connect" goto connect
if /i "%~1"=="status"  goto status
if /i "%~1"=="clean"   goto clean
if /i "%~1"=="install" goto install
if /i "%~1"=="shell"   goto shell
echo Usage: tv-adb.cmd connect ^| status ^| clean ^| install ^| shell
exit /b 1

:connect
"%ADB%" connect %TV%
"%ADB%" devices
goto :eof

:status
"%ADB%" -s %TV% shell "getprop ro.build.version.release; cat /proc/meminfo"
"%ADB%" -s %TV% shell "dumpsys meminfo"
goto :eof

:clean
echo [*] freeing background apps...
"%ADB%" -s %TV% shell "am force-stop com.netflix.ninja"
"%ADB%" -s %TV% shell "am force-stop com.android.vending"
"%ADB%" -s %TV% shell "am force-stop org.smarttube.stable"
"%ADB%" -s %TV% shell "pm trim-caches 2000"
"%ADB%" -s %TV% shell "dumpsys meminfo"
goto :eof

:install
if "%~2"=="" ( echo Usage: tv-adb.cmd install ^<file.apk^> & exit /b 1 )
"%ADB%" -s %TV% install -r "%~2"
goto :eof

:shell
if "%~2"=="" ( echo Usage: tv-adb.cmd shell "cmd" & exit /b 1 )
"%ADB%" -s %TV% shell %2
goto :eof
