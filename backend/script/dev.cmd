@echo off
cd /d %~dp0\..
set PYTHONPATH=%CD%
set DEBUG=true
uvicorn main:app --reload --reload-dir "%CD%" --port 8000
