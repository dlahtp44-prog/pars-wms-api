
@echo off
cd /d %~dp0backend
py -3.11 -m uvicorn app:app --reload
pause
