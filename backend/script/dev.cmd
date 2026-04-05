@echo off
cd /d %~dp0\..
set PYTHONPATH=%CD%
uvicorn main:app --reload --port 8000
