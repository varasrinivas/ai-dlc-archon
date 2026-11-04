@echo off
rem The one verification command for this workspace (Windows twin of verify.sh).
rem priorauth-api depends on priorauth-aging: install the library first, then test the API.
cd /d "%~dp0..\priorauth-aging" && call mvn -q install && cd /d "%~dp0..\priorauth-api" && call mvn -q test
