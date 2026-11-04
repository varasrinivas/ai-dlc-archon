@echo off
rem Windows twin of verify.sh, for running the checks by hand in cmd or PowerShell.
cd /d "%~dp0.." && mvn -q test
